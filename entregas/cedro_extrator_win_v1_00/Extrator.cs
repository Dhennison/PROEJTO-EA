// Extrator de texto; nao interpreta campos de negocio nem calcula o Modelo D.
using System;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Globalization;
using System.Security.Cryptography;
using System.Collections.Generic;

public static class CedroWin100 {
    static readonly Encoding Utf8 = new UTF8Encoding(false, true);
    const string Header = "linha_original|ativo|data_hora|campo3|campo4|campo5|campo6|campo7|campo8";
    sealed class Stats {
        public long Count, Regressions, Equal, Invalid, WrongDate, Fields;
        public string Previous = "", First = "", Last = "";
    }
    sealed class Parts : IDisposable {
        readonly string folder, day;
        readonly long limit;
        public readonly List<string> Files = new List<string>();
        FileStream file; ZipArchive zip; StreamWriter writer;
        public Parts(string folder, string day, long limit) { this.folder=folder; this.day=day; this.limit=limit; }
        void Open() {
            string path=Path.Combine(folder, "WIN_"+day+"_parte"+(Files.Count+1).ToString("D3")+".zip");
            file=new FileStream(path, FileMode.CreateNew, FileAccess.Write);
            Files.Add(path);
            zip=new ZipArchive(file, ZipArchiveMode.Create, true);
            writer=new StreamWriter(zip.CreateEntry("WIN_"+day+".txt", CompressionLevel.Optimal).Open(), Utf8, 65536);
            writer.WriteLine(Header);
        }
        public void Write(long n, string line) {
            if(Utf8.GetByteCount(line)>1048576) throw new InvalidDataException("Linha WIN maior que 1 MiB: "+n);
            if(writer==null) Open();
            writer.Write(n.ToString(CultureInfo.InvariantCulture)); writer.Write('|'); writer.WriteLine(line);
            // Flush acompanha o tamanho comprimido, sem manter o dia inteiro na memoria.
            // A verificacao ocorre a cada registro; o limite tem ampla margem ate 32 MiB.
            if((n & 4095)==0) writer.Flush();
            if(file.Position>=limit) Close();
        }
        void Close() {
            if(writer==null) return;
            writer.Dispose(); zip.Dispose(); file.Dispose(); writer=null;
            if(new FileInfo(Files[Files.Count-1]).Length>=28L*1024*1024)
                throw new IOException("Parte excedeu limite de envio. Nao enviar esta execucao.");
        }
        public void Dispose() { Close(); }
    }
    static string Hash(string path) {
        using(var s=File.OpenRead(path)) using(var h=SHA256.Create())
            return BitConverter.ToString(h.ComputeHash(s)).Replace("-", "").ToLowerInvariant();
    }
    static string Cell(string s) { return "\""+s.Replace("\"", "\"\"")+"\""; }
    public static void Run(string[] sources, string[] eods, string output, long partLimit) {
        if(Directory.Exists(output)) throw new IOException("Destino ja existe; escolha uma nova pasta.");
        if(partLimit<=0 || partLimit>24L*1024*1024) throw new ArgumentException("Limite invalido.");
        var dates=new HashSet<string>(); var months=new HashSet<string>();
        foreach(string path in sources) {
            string day=Path.GetFileNameWithoutExtension(path);
            if(!System.Text.RegularExpressions.Regex.IsMatch(day, "^2026(08|09|10)[0-9]{2}$")) throw new ArgumentException("Data invalida.");
            DateTime.ParseExact(day,"yyyyMMdd",CultureInfo.InvariantCulture);
            if(!dates.Add(day)) throw new IOException("Dois arquivos TICK para o mesmo dia: "+day+". Remova a copia da pasta selecionada.");
            months.Add(day.Substring(0,6));
        }
        if(months.Count!=3) throw new IOException("Selecione a pasta comum dos tres meses descompactados: agosto, setembro e outubro de 2026.");
        Directory.CreateDirectory(output);
        string meta=Path.Combine(output,"CONTROLE"); Directory.CreateDirectory(meta);
        File.WriteAllText(Path.Combine(output,"INCOMPLETO.txt"),"Execucao ainda nao concluida. Nao enviar como coleta completa.",Utf8);
        using(var manifest=new StreamWriter(Path.Combine(meta,"ARQUIVOS.csv"),false,Utf8))
        using(var inventory=new StreamWriter(Path.Combine(meta,"CONTRATOS.csv"),false,Utf8)) {
            manifest.WriteLine("tipo;arquivo;bytes;sha256;linhas_total;linhas_WIN");
            inventory.WriteLine("dia;ativo;registros;primeiro_timestamp_na_ordem;ultimo_timestamp_na_ordem;regressoes_timestamp;empates_consecutivos;timestamp_invalido;data_diferente_arquivo;campos_diferentes_de_8");
            Array.Sort(sources, StringComparer.OrdinalIgnoreCase);
            foreach(string path in sources) {
                string day=Path.GetFileNameWithoutExtension(path);
                Console.WriteLine("LENDO "+day+" (todos os contratos WIN)");
                long all=0, selected=0;
                var stats=new SortedDictionary<string,Stats>(StringComparer.Ordinal);
                var before=new FileInfo(path); long bytes=before.Length; DateTime modified=before.LastWriteTimeUtc;
                string sourceHash;
                List<string> parts;
                using(var outputParts=new Parts(output,day,partLimit))
                using(var sha=SHA256.Create())
                using(var input=File.OpenRead(path))
                using(var hashed=new CryptoStream(input,sha,CryptoStreamMode.Read))
                using(var reader=new StreamReader(hashed,Utf8,true,1048576)) {
                    string line;
                    while((line=reader.ReadLine())!=null) {
                        all++;
                        int pipe=line.IndexOf('|');
                        if(pipe<3 || !line.StartsWith("WIN",StringComparison.OrdinalIgnoreCase)) continue;
                        string symbol=line.Substring(0,pipe);
                        selected++; outputParts.Write(all,line);
                        Stats s; if(!stats.TryGetValue(symbol,out s)) { s=new Stats(); stats.Add(symbol,s); }
                        s.Count++;
                        string[] fields=line.Split('|');
                        if(fields.Length!=8) s.Fields++;
                        string stamp=fields.Length>1 ? fields[1] : "";
                        DateTime dt;
                        if(!DateTime.TryParseExact(stamp,"yyyy-MM-dd HH:mm:ss.fff",CultureInfo.InvariantCulture,DateTimeStyles.None,out dt)) s.Invalid++;
                        else {
                            if(dt.ToString("yyyyMMdd",CultureInfo.InvariantCulture)!=day) s.WrongDate++;
                            if(s.Previous!="") { int cmp=String.CompareOrdinal(stamp,s.Previous); if(cmp<0)s.Regressions++; if(cmp==0)s.Equal++; }
                            s.Previous=stamp;
                        }
                        if(s.Count==1)s.First=stamp; s.Last=stamp;
                    }
                    sourceHash=BitConverter.ToString(sha.Hash).Replace("-", "").ToLowerInvariant();
                    parts=outputParts.Files;
                }
                var after=new FileInfo(path);
                if(after.Length!=bytes || after.LastWriteTimeUtc!=modified) throw new IOException("Fonte mudou durante a leitura: "+day);
                manifest.WriteLine("TICK_FONTE;"+Cell(day+".log")+";"+bytes+";"+sourceHash+";"+all+";"+selected);
                foreach(string p in parts) manifest.WriteLine("WIN_ZIP;"+Cell(Path.GetFileName(p))+";"+new FileInfo(p).Length+";"+Hash(p)+";;");
                foreach(var pair in stats) {
                    Stats s=pair.Value;
                    inventory.WriteLine(day+";"+Cell(pair.Key)+";"+s.Count+";"+Cell(s.First)+";"+Cell(s.Last)+";"+s.Regressions+";"+s.Equal+";"+s.Invalid+";"+s.WrongDate+";"+s.Fields);
                }
                if(selected==0) inventory.WriteLine(day+";SEM_WIN;0;;;;;;;");
                manifest.Flush(); inventory.Flush(); Console.WriteLine("OK "+day+": "+selected+" linhas WIN; "+parts.Count+" ZIP(s)");
            }
            // EOD e pequeno: copiar integralmente, sem inferir layout ou ajustar precos.
            int eodIndex=0;
            foreach(string path in eods) {
                string name=(++eodIndex).ToString("D3")+"_"+Path.GetFileName(path);
                string dest=Path.Combine(meta,name); File.Copy(path,dest,false);
                manifest.WriteLine("EOD_COPIA;"+Cell(name)+";"+new FileInfo(dest).Length+";"+Hash(dest)+";;");
            }
        }
        File.WriteAllText(Path.Combine(meta,"LEITURA.txt"),
            "CEDRO WIN v1.00 - extracao de agosto/setembro/outubro 2026.\r\n"+
            "Texto original WIN preservado em UTF-8; finais de linha normalizados.\r\n"+
            "Primeira coluna adicionada: numero de linha no arquivo fonte (nao sequencia oficial).\r\n"+
            "Todos os registros preservados, inclusive repetidos/mesmo milissegundo. Sem ordenar ou filtrar condicoes.\r\n"+
            "Campo3 a campo8 ainda sem interpretacao certificada; fuso nao confirmado.\r\n"+
            "CONTRATOS.csv mostra inventario por data/codigo, regressoes e anomalias. Ausencia de regressao nao prova ordem oficial entre empates.\r\n"+
            "EOD copiado sem interpretacao. Arquivos EOD encontrados: "+eods.Length+".\r\n"+
            "SHA256 TICK_FONTE corresponde a todos os bytes originais, nao apenas ao WIN.\r\n"+
            "Escopo sao os arquivos encontrados; completude de calendario e qualidade serao auditadas no retorno.\r\n"+
            "Nenhum backtest, selecao de contrato, resultado ou preenchimento real foi calculado.\r\n",Utf8);
        string geral=Path.Combine(output,"GERAL_CEDRO_WIN.zip");
        using(var f=new FileStream(geral,FileMode.CreateNew)) using(var z=new ZipArchive(f,ZipArchiveMode.Create)) {
            foreach(string p in Directory.GetFiles(meta)) {
                using(var src=File.OpenRead(p)) using(var dst=z.CreateEntry(Path.GetFileName(p),CompressionLevel.Optimal).Open()) src.CopyTo(dst);
            }
        }
        if(new FileInfo(geral).Length>=28L*1024*1024) throw new IOException("GERAL acima de 28 MiB; avisar antes de enviar.");
        File.WriteAllText(Path.Combine(output,"CONCLUIDO.txt"),"END;EXTRACAO_CONCLUIDA\r\nGERAL_SHA256="+Hash(geral)+"\r\nConcluido nao certifica cobertura de todos os pregoes nem ordem oficial dos negocios.\r\n",Utf8);
        File.Delete(Path.Combine(output,"INCOMPLETO.txt"));
        Console.WriteLine("END;EXTRACAO_CONCLUIDA\nPASTA: "+output);
    }
}
