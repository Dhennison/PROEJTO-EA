#ifndef PM_REFERENCE_110
#define PM_REFERENCE_110
#include "ModeloD_Core.mqh"
#define PM_DAYS 14
#define PM_SLOTS 70
const datetime PM_BEGIN=D'2026.09.01 00:00:00';
const datetime PM_END=D'2026.09.22 00:00:00';
struct PMReference { datetime begin,first,cut,end,last_bar; string date,previous_date; MDInputs values; int expected_bars; };
PMReference pm_ref[PM_DAYS];
void PMInitReference()
{
 // Referencia Work 2026-09-01; nao e consulta de ajuste B3 live.
 pm_ref[0].date="2026-09-01";pm_ref[0].previous_date="2026-08-31";
 pm_ref[0].begin=D'2026.09.01 00:00:00';pm_ref[0].end=D'2026.09.02 00:00:00';
 pm_ref[0].first=D'2026.09.01 09:02:00';pm_ref[0].cut=D'2026.09.01 18:00:00';pm_ref[0].last_bar=D'2026.09.01 18:24:00';
 pm_ref[0].expected_bars=563;
 pm_ref[0].values.high_prev=181230;pm_ref[0].values.low_prev=178610;
 pm_ref[0].values.close_prev=180075;pm_ref[0].values.open_today=179390;pm_ref[0].values.adjustment=180208;
 // Referencia Work 2026-09-02; nao e consulta de ajuste B3 live.
 pm_ref[1].date="2026-09-02";pm_ref[1].previous_date="2026-09-01";
 pm_ref[1].begin=D'2026.09.02 00:00:00';pm_ref[1].end=D'2026.09.03 00:00:00';
 pm_ref[1].first=D'2026.09.02 09:03:00';pm_ref[1].cut=D'2026.09.02 18:00:00';pm_ref[1].last_bar=D'2026.09.02 18:24:00';
 pm_ref[1].expected_bars=562;
 pm_ref[1].values.high_prev=183670;pm_ref[1].values.low_prev=179000;
 pm_ref[1].values.close_prev=182390;pm_ref[1].values.open_today=182050;pm_ref[1].values.adjustment=182233;
 // Referencia Work 2026-09-03; nao e consulta de ajuste B3 live.
 pm_ref[2].date="2026-09-03";pm_ref[2].previous_date="2026-09-02";
 pm_ref[2].begin=D'2026.09.03 00:00:00';pm_ref[2].end=D'2026.09.04 00:00:00';
 pm_ref[2].first=D'2026.09.03 09:02:00';pm_ref[2].cut=D'2026.09.03 18:00:00';pm_ref[2].last_bar=D'2026.09.03 18:24:00';
 pm_ref[2].expected_bars=563;
 pm_ref[2].values.high_prev=188930;pm_ref[2].values.low_prev=181970;
 pm_ref[2].values.close_prev=187900;pm_ref[2].values.open_today=189480;pm_ref[2].values.adjustment=187951;
 // Referencia Work 2026-09-04; nao e consulta de ajuste B3 live.
 pm_ref[3].date="2026-09-04";pm_ref[3].previous_date="2026-09-03";
 pm_ref[3].begin=D'2026.09.04 00:00:00';pm_ref[3].end=D'2026.09.05 00:00:00';
 pm_ref[3].first=D'2026.09.04 09:02:00';pm_ref[3].cut=D'2026.09.04 18:00:00';pm_ref[3].last_bar=D'2026.09.04 18:24:00';
 pm_ref[3].expected_bars=563;
 pm_ref[3].values.high_prev=191480;pm_ref[3].values.low_prev=187215;
 pm_ref[3].values.close_prev=187695;pm_ref[3].values.open_today=187870;pm_ref[3].values.adjustment=187706;
 // Referencia Work 2026-09-08; nao e consulta de ajuste B3 live.
 pm_ref[4].date="2026-09-08";pm_ref[4].previous_date="2026-09-04";
 pm_ref[4].begin=D'2026.09.08 00:00:00';pm_ref[4].end=D'2026.09.09 00:00:00';
 pm_ref[4].first=D'2026.09.08 09:02:00';pm_ref[4].cut=D'2026.09.08 18:00:00';pm_ref[4].last_bar=D'2026.09.08 18:24:00';
 pm_ref[4].expected_bars=563;
 pm_ref[4].values.high_prev=188990;pm_ref[4].values.low_prev=185520;
 pm_ref[4].values.close_prev=187600;pm_ref[4].values.open_today=190480;pm_ref[4].values.adjustment=187410;
 // Referencia Work 2026-09-09; nao e consulta de ajuste B3 live.
 pm_ref[5].date="2026-09-09";pm_ref[5].previous_date="2026-09-08";
 pm_ref[5].begin=D'2026.09.09 00:00:00';pm_ref[5].end=D'2026.09.10 00:00:00';
 pm_ref[5].first=D'2026.09.09 09:03:00';pm_ref[5].cut=D'2026.09.09 18:00:00';pm_ref[5].last_bar=D'2026.09.09 18:24:00';
 pm_ref[5].expected_bars=562;
 pm_ref[5].values.high_prev=191930;pm_ref[5].values.low_prev=188735;
 pm_ref[5].values.close_prev=190025;pm_ref[5].values.open_today=189550;pm_ref[5].values.adjustment=189835;
 // Referencia Work 2026-09-10; nao e consulta de ajuste B3 live.
 pm_ref[6].date="2026-09-10";pm_ref[6].previous_date="2026-09-09";
 pm_ref[6].begin=D'2026.09.10 00:00:00';pm_ref[6].end=D'2026.09.11 00:00:00';
 pm_ref[6].first=D'2026.09.10 09:03:00';pm_ref[6].cut=D'2026.09.10 18:00:00';pm_ref[6].last_bar=D'2026.09.10 18:24:00';
 pm_ref[6].expected_bars=562;
 pm_ref[6].values.high_prev=189750;pm_ref[6].values.low_prev=186895;
 pm_ref[6].values.close_prev=188550;pm_ref[6].values.open_today=187500;pm_ref[6].values.adjustment=188016;
 // Referencia Work 2026-09-11; nao e consulta de ajuste B3 live.
 pm_ref[7].date="2026-09-11";pm_ref[7].previous_date="2026-09-10";
 pm_ref[7].begin=D'2026.09.11 00:00:00';pm_ref[7].end=D'2026.09.12 00:00:00';
 pm_ref[7].first=D'2026.09.11 09:03:00';pm_ref[7].cut=D'2026.09.11 18:00:00';pm_ref[7].last_bar=D'2026.09.11 18:24:00';
 pm_ref[7].expected_bars=562;
 pm_ref[7].values.high_prev=190780;pm_ref[7].values.low_prev=186275;
 pm_ref[7].values.close_prev=190465;pm_ref[7].values.open_today=191060;pm_ref[7].values.adjustment=190412;
 // Referencia Work 2026-09-14; nao e consulta de ajuste B3 live.
 pm_ref[8].date="2026-09-14";pm_ref[8].previous_date="2026-09-11";
 pm_ref[8].begin=D'2026.09.14 00:00:00';pm_ref[8].end=D'2026.09.15 00:00:00';
 pm_ref[8].first=D'2026.09.14 09:03:00';pm_ref[8].cut=D'2026.09.14 18:00:00';pm_ref[8].last_bar=D'2026.09.14 18:24:00';
 pm_ref[8].expected_bars=562;
 pm_ref[8].values.high_prev=191345;pm_ref[8].values.low_prev=188075;
 pm_ref[8].values.close_prev=188720;pm_ref[8].values.open_today=186900;pm_ref[8].values.adjustment=188987;
 // Referencia Work 2026-09-15; nao e consulta de ajuste B3 live.
 pm_ref[9].date="2026-09-15";pm_ref[9].previous_date="2026-09-14";
 pm_ref[9].begin=D'2026.09.15 00:00:00';pm_ref[9].end=D'2026.09.16 00:00:00';
 pm_ref[9].first=D'2026.09.15 09:03:00';pm_ref[9].cut=D'2026.09.15 18:00:00';pm_ref[9].last_bar=D'2026.09.15 18:24:00';
 pm_ref[9].expected_bars=562;
 pm_ref[9].values.high_prev=188260;pm_ref[9].values.low_prev=185040;
 pm_ref[9].values.close_prev=187250;pm_ref[9].values.open_today=186910;pm_ref[9].values.adjustment=187507;
 // Referencia Work 2026-09-16; nao e consulta de ajuste B3 live.
 pm_ref[10].date="2026-09-16";pm_ref[10].previous_date="2026-09-15";
 pm_ref[10].begin=D'2026.09.16 00:00:00';pm_ref[10].end=D'2026.09.17 00:00:00';
 pm_ref[10].first=D'2026.09.16 09:02:00';pm_ref[10].cut=D'2026.09.16 18:00:00';pm_ref[10].last_bar=D'2026.09.16 18:24:00';
 pm_ref[10].expected_bars=563;
 pm_ref[10].values.high_prev=189555;pm_ref[10].values.low_prev=186775;
 pm_ref[10].values.close_prev=188510;pm_ref[10].values.open_today=189320;pm_ref[10].values.adjustment=188393;
 // Referencia Work 2026-09-17; nao e consulta de ajuste B3 live.
 pm_ref[11].date="2026-09-17";pm_ref[11].previous_date="2026-09-16";
 pm_ref[11].begin=D'2026.09.17 00:00:00';pm_ref[11].end=D'2026.09.18 00:00:00';
 pm_ref[11].first=D'2026.09.17 09:02:00';pm_ref[11].cut=D'2026.09.17 18:00:00';pm_ref[11].last_bar=D'2026.09.17 18:24:00';
 pm_ref[11].expected_bars=563;
 pm_ref[11].values.high_prev=189730;pm_ref[11].values.low_prev=186410;
 pm_ref[11].values.close_prev=187600;pm_ref[11].values.open_today=188810;pm_ref[11].values.adjustment=187236;
 // Referencia Work 2026-09-18; nao e consulta de ajuste B3 live.
 pm_ref[12].date="2026-09-18";pm_ref[12].previous_date="2026-09-17";
 pm_ref[12].begin=D'2026.09.18 00:00:00';pm_ref[12].end=D'2026.09.19 00:00:00';
 pm_ref[12].first=D'2026.09.18 09:03:00';pm_ref[12].cut=D'2026.09.18 18:00:00';pm_ref[12].last_bar=D'2026.09.18 18:24:00';
 pm_ref[12].expected_bars=562;
 pm_ref[12].values.high_prev=189085;pm_ref[12].values.low_prev=184465;
 pm_ref[12].values.close_prev=188280;pm_ref[12].values.open_today=187905;pm_ref[12].values.adjustment=187733;
 // Referencia Work 2026-09-21; nao e consulta de ajuste B3 live.
 pm_ref[13].date="2026-09-21";pm_ref[13].previous_date="2026-09-18";
 pm_ref[13].begin=D'2026.09.21 00:00:00';pm_ref[13].end=D'2026.09.22 00:00:00';
 pm_ref[13].first=D'2026.09.21 09:02:00';pm_ref[13].cut=D'2026.09.21 18:00:00';pm_ref[13].last_bar=D'2026.09.21 18:24:00';
 pm_ref[13].expected_bars=563;
 pm_ref[13].values.high_prev=188730;pm_ref[13].values.low_prev=185880;
 pm_ref[13].values.close_prev=187135;pm_ref[13].values.open_today=187980;pm_ref[13].values.adjustment=186745;
}
#endif
