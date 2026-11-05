//+------------------------------------------------------------------+
//| DiagTicksAB.mq5  v1.21                                           |
//| Consulta somente leitura: mesma janela, mesmo CopyTicksRange,    |
//| no terminal (A) e no Tester (B). Nao envia ordens, nao altera    |
//| historico e nao usa nenhuma biblioteca do Modelo D.              |
//|                                                                  |
//| Contagens separadas:                                             |
//|  tf_n  = flags & (LAST|VOLUME|BUY|SELL) != 0                     |
//|  ea_n  = tf_n E last>0 e finito  (criterio de aceite do EA v2.11)|
//|  tf_last_invalido = tf_n com last<=0 ou invalido (o EA rejeitaria|
//|                     o retorno inteiro nesse caso)                |
//|  carregado_sem_flag = last/volume preenchidos SEM flag de negocio|
//| ESTAVEL exige duas leituras validas iguais campo a campo.        |
//| Hashes sao resumos; nao autorizam estabilidade sozinhos.         |
//| InpDumpCsv grava o snapshot ALL final, com tamanho conferido.    |
//+------------------------------------------------------------------+
#property version "1.21"

input string   InpSymbol      = "WINZ26";
input datetime InpFrom        = D'2026.10.30 09:00:00'; // hora do servidor
input datetime InpTo          = D'2026.10.30 09:10:00'; // max. 60 min
input int      InpMaxAttempts = 10;                     // releituras ate estabilizar
input string   InpTag         = "";                     // ex.: XP_01, GENIAL_01
input bool     InpDumpCsv     = false;                  // grava todos os ticks ALL da leitura final

#define NF 64
#define NMIN 60

struct Res
  {
   bool   same_ticks;           // igualdade campo a campo com a leitura valida anterior
   bool   valid;                // retorno consistente (ver Collect)
   string why;                  // motivo se invalido
   int    n, err, nf, tf_n, ea_n, tf_last_invalido, carried_n, last_pos, vol_pos;
   long   fv[NF];
   int    fc[NF];
   long   first_tf_msc;
   ulong  full_hash;            // TODOS os registros: msc,bid,ask,last,volume,volume_real,flags
   ulong  tf_hash;              // somente registros com flag de negocio
   int    per_min[NMIN];        // registros com flag de negocio por minuto
   long   first_msc, last_msc;
   double first_last, first_bid, first_ask;
   uint   first_flags;
  };

Res      g_a, g_tr, g_in, g_pa, g_ptr, g_pin;
MqlTick  g_all_ticks[];
MqlTick  g_trade_ticks[], g_info_ticks[];
bool     g_have = false, g_done = false;
int      g_attempt = 0;
string   g_out = "";
uint     g_mask = 0;

void Say(const string s) { Print(s); g_out += s + "\r\n"; }

string Clean(const string s)
  {
   string o = "";
   for(int i = 0; i < StringLen(s); i++)
     {
      ushort c = StringGetCharacter(s, i);
      if((c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '-')
         o += ShortToString(c);
      else
         o += "_";
     }
   return o;
  }

string Env() { return MQLInfoInteger(MQL_TESTER) ? "TESTER" : "TERMINAL"; }

void Mix(ulong &h, const ulong v) { h ^= v; h *= 1099511628211; }
// Hash e somente resumo. A estabilidade usa SameTicks, sem arredondamento.
ulong Q(const double x)
  {
   string text = DoubleToString(x, -16);
   ulong h = 1469598103934665603;
   for(int i = 0; i < StringLen(text); i++) Mix(h, (ulong)StringGetCharacter(text, i));
   return h;
  }

bool SameTicks(const MqlTick &x[], const MqlTick &y[])
  {
   int n = ArraySize(x);
   if(n != ArraySize(y)) return false;
   for(int i = 0; i < n; i++)
      if(x[i].time != y[i].time || x[i].time_msc != y[i].time_msc ||
         x[i].bid != y[i].bid || x[i].ask != y[i].ask || x[i].last != y[i].last ||
         x[i].volume != y[i].volume || x[i].volume_real != y[i].volume_real || x[i].flags != y[i].flags)
         return false;
   return true;
  }

bool StoreTicks(const MqlTick &src[], MqlTick &dst[])
  {
   int n = ArraySize(src);
   if(ArrayResize(dst, n) != n) return false;
   if(n == 0) return true;
   return ArrayCopy(dst, src) == n;
  }

int OnInit()
  {
   g_mask = (uint)TICK_FLAG_LAST | (uint)TICK_FLAG_VOLUME | (uint)TICK_FLAG_BUY | (uint)TICK_FLAG_SELL;
   if(InpFrom <= 0 || InpTo <= InpFrom || (InpTo - InpFrom) > NMIN * 60)
     { Print("DiagTicksAB: janela invalida (From<To e no maximo 60 min)."); return INIT_PARAMETERS_INCORRECT; }
   if(InpMaxAttempts < 2)
     { Print("DiagTicksAB: InpMaxAttempts deve ser >= 2."); return INIT_PARAMETERS_INCORRECT; }
   if(!SymbolSelect(InpSymbol, true))
     { Print("DiagTicksAB: SymbolSelect falhou para ", InpSymbol, " erro=", GetLastError()); return INIT_FAILED; }
   if(!EventSetTimer(1))
     { Print("DiagTicksAB: EventSetTimer falhou erro=", GetLastError()); return INIT_FAILED; }
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason) { EventKillTimer(); }

void Collect(const uint mode, Res &r)
  {
   r.valid = false; r.same_ticks = false; r.why = "";
   r.n = 0; r.err = 0; r.nf = 0; r.tf_n = 0; r.ea_n = 0; r.tf_last_invalido = 0;
   r.carried_n = 0; r.last_pos = 0; r.vol_pos = 0;
   r.first_tf_msc = 0; r.full_hash = 1469598103934665603; r.tf_hash = 1469598103934665603;
   r.first_msc = 0; r.last_msc = 0; r.first_last = 0; r.first_bid = 0; r.first_ask = 0; r.first_flags = 0;
   for(int m = 0; m < NMIN; m++) r.per_min[m] = 0;

   MqlTick t[];
   ulong a = (ulong)InpFrom * 1000;
   ulong b = (ulong)InpTo * 1000 - 1;
   ResetLastError();
   r.n = CopyTicksRange(InpSymbol, t, mode, a, b);
   r.err = GetLastError();
   if(r.n < 0)              { r.why = "RETORNO_NEGATIVO"; return; }
   if(r.err != 0)           { r.why = "ERRO_" + IntegerToString(r.err); return; }
   if(r.n != ArraySize(t))  { r.why = "N_DIFERENTE_DO_ARRAY(n=" + IntegerToString(r.n) + ",array=" + IntegerToString(ArraySize(t)) + ")"; return; }

   bool ok = true;
   long prev = -1;
   if(r.n > 0)
     {
      r.first_msc = t[0].time_msc; r.last_msc = t[r.n - 1].time_msc;
      r.first_last = t[0].last; r.first_bid = t[0].bid; r.first_ask = t[0].ask; r.first_flags = t[0].flags;
     }

   for(int i = 0; i < r.n; i++)
     {
      // Validar antes de comparar, converter ou gerar hash de campos numericos.
      if(!MathIsValidNumber(t[i].bid) || !MathIsValidNumber(t[i].ask) ||
         !MathIsValidNumber(t[i].last) || !MathIsValidNumber(t[i].volume_real))
        {
         r.why = "CAMPO_NAO_FINITO(i=" + IntegerToString(i) + ")";
         if((t[i].flags & g_mask) != 0)
           {
            r.tf_n++;
            if(!MathIsValidNumber(t[i].last)) r.tf_last_invalido++;
           }
         return;
        }
      // mesmas checagens estruturais do EA: dentro da janela e sem retrocesso de tempo
      if(t[i].time_msc < 0 || (ulong)t[i].time_msc < a || (ulong)t[i].time_msc > b || t[i].time_msc < prev)
        { if(ok) r.why = "FORA_DA_JANELA_OU_FORA_DE_ORDEM(i=" + IntegerToString(i) + ")"; ok = false; }
      prev = t[i].time_msc;

      int k = -1;
      for(int j = 0; j < r.nf; j++) if(r.fv[j] == (long)t[i].flags) { k = j; break; }
      if(k < 0 && r.nf < NF) { k = r.nf++; r.fv[k] = (long)t[i].flags; r.fc[k] = 0; }
      if(k >= 0) r.fc[k]++;

      if(t[i].last > 0)   r.last_pos++;
      if(t[i].volume > 0) r.vol_pos++;

      // hash de TODOS os campos de TODOS os registros
      Mix(r.full_hash, (ulong)t[i].time_msc);
      Mix(r.full_hash, Q(t[i].bid));
      Mix(r.full_hash, Q(t[i].ask));
      Mix(r.full_hash, Q(t[i].last));
      Mix(r.full_hash, (ulong)t[i].volume);
      Mix(r.full_hash, Q(t[i].volume_real));
      Mix(r.full_hash, (ulong)t[i].flags);

      bool tf = ((t[i].flags & g_mask) != 0);
      if(tf)
        {
         r.tf_n++;
         if(r.first_tf_msc == 0) r.first_tf_msc = t[i].time_msc;
         int mn = (int)(((ulong)t[i].time_msc - a) / 60000);
         if(mn >= 0 && mn < NMIN) r.per_min[mn]++;
         Mix(r.tf_hash, (ulong)t[i].time_msc);
         Mix(r.tf_hash, Q(t[i].last));
         Mix(r.tf_hash, (ulong)t[i].volume);
         Mix(r.tf_hash, (ulong)t[i].flags);
         if(MathIsValidNumber(t[i].last) && t[i].last > 0) r.ea_n++;
         else r.tf_last_invalido++;
        }
      else if(t[i].last > 0 || t[i].volume > 0)
         r.carried_n++;
     }

   if(!ok) return;
   bool stored = false;
   if(mode == COPY_TICKS_ALL)
     { r.same_ticks = SameTicks(t, g_all_ticks); stored = StoreTicks(t, g_all_ticks); }
   else if(mode == COPY_TICKS_TRADE)
     { r.same_ticks = SameTicks(t, g_trade_ticks); stored = StoreTicks(t, g_trade_ticks); }
   else
     { r.same_ticks = SameTicks(t, g_info_ticks); stored = StoreTicks(t, g_info_ticks); }
   if(!stored) { r.why = "FALHA_COPIA_SNAPSHOT"; return; }
   r.valid = true;
  }

bool SameRes(const Res &x, const Res &y)
  {
   return x.valid && y.valid && x.same_ticks && x.n == y.n && x.full_hash == y.full_hash && x.tf_hash == y.tf_hash &&
          x.tf_n == y.tf_n && x.ea_n == y.ea_n && x.tf_last_invalido == y.tf_last_invalido &&
          x.carried_n == y.carried_n && x.first_msc == y.first_msc && x.last_msc == y.last_msc;
  }

void Show(const string tag, const Res &r)
  {
   Say(StringFormat("[%s] valido=%d%s | n=%d err=%d | tf_n=%d | ea_n(last>0 finito)=%d | tf_last_invalido=%d | carregado_sem_flag=%d | last>0=%d | volume>0=%d | primeiro_neg_msc=%I64d",
                    tag, (int)r.valid, (r.valid ? "" : "(" + r.why + ")"), r.n, r.err, r.tf_n, r.ea_n, r.tf_last_invalido,
                    r.carried_n, r.last_pos, r.vol_pos, r.first_tf_msc));
   Say(StringFormat("   hash_completo=%I64u | hash_negocios=%I64u", r.full_hash, r.tf_hash));
   string h = "   flags:";
   for(int j = 0; j < r.nf; j++) h += StringFormat(" %I64d x%d;", r.fv[j], r.fc[j]);
   Say(h);
   string pm = "   neg_por_minuto(tf):";
   int mins = (int)((InpTo - InpFrom) / 60);
   for(int m = 0; m < mins && m < NMIN; m++) pm += StringFormat(" %d", r.per_min[m]);
   Say(pm);
   if(r.n > 0)
      Say(StringFormat("   primeiro_tick: msc=%I64d bid=%.1f ask=%.1f last=%.1f flags=%u | ultimo_msc=%I64d",
                       r.first_msc, r.first_bid, r.first_ask, r.first_last, r.first_flags, r.last_msc));
  }

void Header()
  {
   Say("=== DiagTicksAB v1.21 | ambiente=" + Env() + " | tag=" + InpTag);
   Say("simbolo_consultado=" + InpSymbol + " | simbolo_do_grafico=" + _Symbol + " | periodo=" + EnumToString((ENUM_TIMEFRAMES)_Period));
   Say("janela=" + TimeToString(InpFrom, TIME_DATE | TIME_SECONDS) + " -> " + TimeToString(InpTo, TIME_DATE | TIME_SECONDS) + " (hora do servidor)");
   Say("servidor=" + AccountInfoString(ACCOUNT_SERVER) + " | empresa=" + AccountInfoString(ACCOUNT_COMPANY) + " | build=" + (string)TerminalInfoInteger(TERMINAL_BUILD));
   long cust = 0; SymbolInfoInteger(InpSymbol, SYMBOL_CUSTOM, cust);
   Say(StringFormat("tester=%d visual=%d otimizacao=%d conectado=%d simbolo_custom=%d TimeCurrent=%s",
                    (int)MQLInfoInteger(MQL_TESTER), (int)MQLInfoInteger(MQL_VISUAL_MODE), (int)MQLInfoInteger(MQL_OPTIMIZATION),
                    (int)TerminalInfoInteger(TERMINAL_CONNECTED), (int)cust, TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS)));
  }

bool DumpCsv(const string base)
  {
   int n = g_a.n;
   if(!g_a.valid || n < 0 || ArraySize(g_all_ticks) != n)
     { Print("CSV NAO GRAVADO: snapshot inconsistente com ALL.n"); return false; }
   string fn = base + "_ALL.csv";
   for(int k = 1; FileIsExist(fn, FILE_COMMON) && k < 100; k++) fn = base + "_ALL_" + IntegerToString(k) + ".csv";
   if(FileIsExist(fn, FILE_COMMON))
     { Print("CSV NAO GRAVADO: nomes disponiveis esgotados"); return false; }
   int h = FileOpen(fn, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(h == INVALID_HANDLE) { Print("DiagTicksAB: nao foi possivel gravar o CSV, erro=", GetLastError()); return false; }
   ResetLastError();
   uint header_bytes = FileWriteString(h, "time_msc;bid;ask;last;volume;volume_real;flags\r\n");
   bool ok = header_bytes > 0 && GetLastError() == 0;
   int written = 0;
   for(int i = 0; ok && i < n; i++)
     {
      string row = StringFormat("%I64d;%s;%s;%s;%I64u;%s;%u\r\n", g_all_ticks[i].time_msc, DoubleToString(g_all_ticks[i].bid,-16),
                               DoubleToString(g_all_ticks[i].ask,-16), DoubleToString(g_all_ticks[i].last,-16),
                               g_all_ticks[i].volume, DoubleToString(g_all_ticks[i].volume_real,-16), g_all_ticks[i].flags);
      ResetLastError();
      uint count = FileWriteString(h, row);
      ok = count > 0 && count == (uint)StringLen(row) && GetLastError() == 0;
      if(ok) written++;
     }
   ResetLastError(); FileFlush(h);
   if(GetLastError() != 0) ok = false;
   FileClose(h);
   if(!ok || written != n)
     { Print("CSV INCOMPLETO - NAO USAR: ", fn, " linhas=", written, " esperado=", n); return false; }
   Print("CSV gravado em Common\\Files\\", fn, " linhas_dados=", written, " esperado_ALL_n=", n);
   return true;
  }

void Finish(const bool stable)
  {
   g_done = true;
   string head = g_out; g_out = "";
   Header();
   Say(stable ? "STATUS=ESTAVEL (duas leituras consecutivas validas, comparacao exata campo a campo)"
              : "STATUS=NAO_ESTAVEL_OU_INVALIDO apos " + IntegerToString(g_attempt) + " tentativas - NAO sustenta conclusao de ausencia de negocios");
   Show("ALL",   g_a);
   Show("TRADE", g_tr);
   Show("INFO",  g_in);
   Say(StringFormat("CRUZAMENTO: ALL.tf_n=%d | ALL.ea_n=%d | TRADE.n=%d | TRADE.tf_n=%d | hash_negocios ALL==TRADE: %s",
                    g_a.tf_n, g_a.ea_n, g_tr.n, g_tr.tf_n, (g_a.tf_hash == g_tr.tf_hash ? "sim" : "nao")));
   Say("--- historico das tentativas ---");
   g_out += head;

   string base = "DiagTicksAB_" + Env() + "_" + Clean(AccountInfoString(ACCOUNT_SERVER)) + "_" + Clean(InpSymbol) + "_" +
                 Clean(TimeToString(InpFrom, TIME_DATE | TIME_MINUTES)) + "_" + Clean(TimeToString(InpTo, TIME_DATE | TIME_MINUTES)) +
                 (InpTag != "" ? "_" + Clean(InpTag) : "") + "_" + (string)GetTickCount64();
   string fn = base + ".txt";
   for(int k = 1; FileIsExist(fn, FILE_COMMON) && k < 100; k++) fn = base + "_" + IntegerToString(k) + ".txt";
   if(FileIsExist(fn, FILE_COMMON))
     { Print("Relatorio NAO GRAVADO: nomes disponiveis esgotados"); ExpertRemove(); return; }
   int h = FileOpen(fn, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(h != INVALID_HANDLE) { FileWriteString(h, g_out); FileClose(h); Print("Relatorio gravado em Common\\Files\\", fn); }
   else Print("DiagTicksAB: nao foi possivel gravar o relatorio, erro=", GetLastError());

   if(InpDumpCsv && g_a.valid && ArraySize(g_all_ticks) == g_a.n) DumpCsv(base);
   ExpertRemove();
  }

void OnTimer()
  {
   if(g_done) return;
   if(TimeCurrent() < InpTo + 2) return;   // no Tester espera o relogio simulado passar da janela

   g_attempt++;
   Collect(COPY_TICKS_ALL,   g_a);
   Collect(COPY_TICKS_TRADE, g_tr);
   Collect(COPY_TICKS_INFO,  g_in);

   bool ok   = (g_a.valid && g_tr.valid && g_in.valid);
   bool same = (ok && g_have && SameRes(g_a, g_pa) && SameRes(g_tr, g_ptr) && SameRes(g_in, g_pin));

   Say(StringFormat("tentativa %d | validos ALL=%d TRADE=%d INFO=%d | ALL n=%d err=%d tf=%d ea=%d | TRADE n=%d err=%d | INFO n=%d err=%d | igual_a_anterior=%d%s%s%s",
                    g_attempt, (int)g_a.valid, (int)g_tr.valid, (int)g_in.valid, g_a.n, g_a.err, g_a.tf_n, g_a.ea_n,
                    g_tr.n, g_tr.err, g_in.n, g_in.err, (int)same,
                    (g_a.valid ? "" : " | ALL:" + g_a.why), (g_tr.valid ? "" : " | TRADE:" + g_tr.why), (g_in.valid ? "" : " | INFO:" + g_in.why)));

   if(same || g_attempt >= InpMaxAttempts) { Finish(same); return; }

   g_have = ok;
   if(ok) { g_pa = g_a; g_ptr = g_tr; g_pin = g_in; }
  }
