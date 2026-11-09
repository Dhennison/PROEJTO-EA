#ifndef PM_WORK_REPORT_110
#define PM_WORK_REPORT_110
// SOMENTE RELATORIO. Proibido usar resultado futuro para decidir ordens.
struct PMWorkResult { bool exists,ambiguous; double points; string points_text,reason,entry_time,exit_time; };
PMWorkResult pm_work[PM_SLOTS];
void PMInitWorkReport()
{
 for(int s=0;s<PM_SLOTS;s++){pm_work[s].exists=false;pm_work[s].ambiguous=false;pm_work[s].points=0;pm_work[s].points_text="";pm_work[s].reason="SEM_OPERACAO";pm_work[s].entry_time="";pm_work[s].exit_time="";}
 pm_work[3].exists=true;pm_work[3].ambiguous=false;pm_work[3].points=-375;pm_work[3].points_text="-375";
 pm_work[3].reason="STOP";pm_work[3].entry_time="09:51:00";pm_work[3].exit_time="10:00:00";
 pm_work[4].exists=true;pm_work[4].ambiguous=false;pm_work[4].points=112.414667;pm_work[4].points_text="112.414667";
 pm_work[4].reason="ALVO";pm_work[4].entry_time="10:00:00";pm_work[4].exit_time="10:00:00";
 pm_work[8].exists=true;pm_work[8].ambiguous=false;pm_work[8].points=-375;pm_work[8].points_text="-375";
 pm_work[8].reason="STOP";pm_work[8].entry_time="10:26:00";pm_work[8].exit_time="10:29:00";
 pm_work[9].exists=true;pm_work[9].ambiguous=false;pm_work[9].points=-450;pm_work[9].points_text="-450";
 pm_work[9].reason="STOP";pm_work[9].entry_time="10:42:00";pm_work[9].exit_time="10:50:00";
 pm_work[15].exists=true;pm_work[15].ambiguous=false;pm_work[15].points=379.794667;pm_work[15].points_text="379.794667";
 pm_work[15].reason="ALVO";pm_work[15].entry_time="10:27:00";pm_work[15].exit_time="10:30:00";
 pm_work[18].exists=true;pm_work[18].ambiguous=false;pm_work[18].points=485.790667;pm_work[18].points_text="485.790667";
 pm_work[18].reason="ALVO";pm_work[18].entry_time="13:18:00";pm_work[18].exit_time="13:59:00";
 pm_work[24].exists=true;pm_work[24].ambiguous=false;pm_work[24].points=399.43;pm_work[24].points_text="399.43";
 pm_work[24].reason="ALVO";pm_work[24].entry_time="10:47:00";pm_work[24].exit_time="10:49:00";
 pm_work[25].exists=true;pm_work[25].ambiguous=false;pm_work[25].points=269.005;pm_work[25].points_text="269.005";
 pm_work[25].reason="ALVO";pm_work[25].entry_time="10:18:00";pm_work[25].exit_time="10:20:00";
 pm_work[26].exists=true;pm_work[26].ambiguous=false;pm_work[26].points=-375;pm_work[26].points_text="-375";
 pm_work[26].reason="STOP";pm_work[26].entry_time="11:46:00";pm_work[26].exit_time="12:01:00";
 pm_work[27].exists=true;pm_work[27].ambiguous=false;pm_work[27].points=-650;pm_work[27].points_text="-650";
 pm_work[27].reason="STOP";pm_work[27].entry_time="12:01:00";pm_work[27].exit_time="12:21:00";
 pm_work[30].exists=true;pm_work[30].ambiguous=false;pm_work[30].points=235.011333;pm_work[30].points_text="235.011333";
 pm_work[30].reason="ALVO";pm_work[30].entry_time="09:07:00";pm_work[30].exit_time="09:07:00";
 pm_work[31].exists=true;pm_work[31].ambiguous=false;pm_work[31].points=379.881333;pm_work[31].points_text="379.881333";
 pm_work[31].reason="ALVO";pm_work[31].entry_time="09:09:00";pm_work[31].exit_time="09:14:00";
 pm_work[33].exists=true;pm_work[33].ambiguous=false;pm_work[33].points=-375;pm_work[33].points_text="-375";
 pm_work[33].reason="STOP";pm_work[33].entry_time="11:35:00";pm_work[33].exit_time="11:41:00";
 pm_work[34].exists=true;pm_work[34].ambiguous=false;pm_work[34].points=146.949333;pm_work[34].points_text="146.949333";
 pm_work[34].reason="ALVO";pm_work[34].entry_time="11:45:00";pm_work[34].exit_time="11:45:00";
 pm_work[35].exists=true;pm_work[35].ambiguous=false;pm_work[35].points=187.269333;pm_work[35].points_text="187.269333";
 pm_work[35].reason="ALVO";pm_work[35].entry_time="09:26:00";pm_work[35].exit_time="09:26:00";
 pm_work[36].exists=true;pm_work[36].ambiguous=false;pm_work[36].points=302.709333;pm_work[36].points_text="302.709333";
 pm_work[36].reason="ALVO";pm_work[36].entry_time="09:30:00";pm_work[36].exit_time="09:30:00";
 pm_work[37].exists=true;pm_work[37].ambiguous=false;pm_work[37].points=302.709333;pm_work[37].points_text="302.709333";
 pm_work[37].reason="ALVO";pm_work[37].entry_time="09:30:00";pm_work[37].exit_time="09:30:00";
 pm_work[40].exists=true;pm_work[40].ambiguous=false;pm_work[40].points=439.241;pm_work[40].points_text="439.241";
 pm_work[40].reason="ALVO";pm_work[40].entry_time="09:03:00";pm_work[40].exit_time="09:03:00";
 pm_work[41].exists=true;pm_work[41].ambiguous=false;pm_work[41].points=-375;pm_work[41].points_text="-375";
 pm_work[41].reason="STOP";pm_work[41].entry_time="09:09:00";pm_work[41].exit_time="09:11:00";
 pm_work[42].exists=true;pm_work[42].ambiguous=false;pm_work[42].points=710.006;pm_work[42].points_text="710.006";
 pm_work[42].reason="ALVO";pm_work[42].entry_time="09:15:00";pm_work[42].exit_time="09:56:00";
 pm_work[48].exists=true;pm_work[48].ambiguous=false;pm_work[48].points=-375;pm_work[48].points_text="-375";
 pm_work[48].reason="STOP";pm_work[48].entry_time="12:23:00";pm_work[48].exit_time="12:30:00";
 pm_work[49].exists=true;pm_work[49].ambiguous=false;pm_work[49].points=178.357;pm_work[49].points_text="178.357";
 pm_work[49].reason="ALVO";pm_work[49].entry_time="13:54:00";pm_work[49].exit_time="14:03:00";
 pm_work[50].exists=true;pm_work[50].ambiguous=false;pm_work[50].points=118.479;pm_work[50].points_text="118.479";
 pm_work[50].reason="ALVO";pm_work[50].entry_time="10:00:00";pm_work[50].exit_time="10:00:00";
 pm_work[51].exists=true;pm_work[51].ambiguous=false;pm_work[51].points=191.514;pm_work[51].points_text="191.514";
 pm_work[51].reason="ALVO";pm_work[51].entry_time="10:01:00";pm_work[51].exit_time="10:01:00";
 pm_work[52].exists=true;pm_work[52].ambiguous=false;pm_work[52].points=191.514;pm_work[52].points_text="191.514";
 pm_work[52].reason="ALVO";pm_work[52].entry_time="10:17:00";pm_work[52].exit_time="10:17:00";
 pm_work[58].exists=true;pm_work[58].ambiguous=false;pm_work[58].points=668.777333;pm_work[58].points_text="668.777333";
 pm_work[58].reason="ALVO";pm_work[58].entry_time="09:09:00";pm_work[58].exit_time="09:39:00";
 pm_work[55].exists=true;pm_work[55].ambiguous=false;pm_work[55].points=150.331333;pm_work[55].points_text="150.331333";
 pm_work[55].reason="ALVO";pm_work[55].entry_time="10:33:00";pm_work[55].exit_time="10:33:00";
 pm_work[57].exists=true;pm_work[57].ambiguous=false;pm_work[57].points=243.001333;pm_work[57].points_text="243.001333";
 pm_work[57].reason="ALVO";pm_work[57].entry_time="10:34:00";pm_work[57].exit_time="10:34:00";
 pm_work[56].exists=true;pm_work[56].ambiguous=false;pm_work[56].points=-375;pm_work[56].points_text="-375";
 pm_work[56].reason="STOP";pm_work[56].entry_time="10:34:00";pm_work[56].exit_time="10:36:00";
 pm_work[60].exists=true;pm_work[60].ambiguous=false;pm_work[60].points=251.460667;pm_work[60].points_text="251.460667";
 pm_work[60].reason="ALVO";pm_work[60].entry_time="09:56:00";pm_work[60].exit_time="10:00:00";
 pm_work[61].exists=true;pm_work[61].ambiguous=false;pm_work[61].points=406.470667;pm_work[61].points_text="406.470667";
 pm_work[61].reason="ALVO";pm_work[61].entry_time="11:24:00";pm_work[61].exit_time="12:04:00";
 pm_work[68].exists=true;pm_work[68].ambiguous=false;pm_work[68].points=579.863333;pm_work[68].points_text="579.863333";
 pm_work[68].reason="ALVO";pm_work[68].entry_time="09:02:00";pm_work[68].exit_time="09:03:00";
 pm_work[69].exists=true;pm_work[69].ambiguous=false;pm_work[69].points=234.328333;pm_work[69].points_text="234.328333";
 pm_work[69].reason="ALVO";pm_work[69].entry_time="09:19:00";pm_work[69].exit_time="09:20:00";
}
#endif
