#property strict
#property indicator_chart_window
#property indicator_buffers 1
#property indicator_color1 clrDodgerBlue

double SmokeBuffer[];

int OnInit()
{
   SetIndexBuffer(0, SmokeBuffer);
   SetIndexStyle(0, DRAW_LINE, STYLE_SOLID, 1, clrDodgerBlue);
   SetIndexLabel(0, "Metafx compile-only smoke");
   return(INIT_SUCCEEDED);
}

int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   if(rates_total < 2)
      return(0);
   int start = prev_calculated > 0 ? prev_calculated - 1 : 0;
   for(int i = start; i < rates_total; i++)
      SmokeBuffer[i] = close[i];
   return(rates_total);
}
