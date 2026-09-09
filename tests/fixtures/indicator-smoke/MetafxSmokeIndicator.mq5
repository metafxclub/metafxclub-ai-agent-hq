#property strict
#property indicator_chart_window
#property indicator_buffers 1
#property indicator_plots 1
#property indicator_label1 "Metafx compile-only smoke"
#property indicator_type1 DRAW_LINE
#property indicator_color1 clrDodgerBlue
#property indicator_style1 STYLE_SOLID
#property indicator_width1 1

double SmokeBuffer[];

int OnInit()
{
   SetIndexBuffer(0, SmokeBuffer, INDICATOR_DATA);
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
