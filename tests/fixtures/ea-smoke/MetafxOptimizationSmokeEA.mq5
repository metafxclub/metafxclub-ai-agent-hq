#property strict

input int SmokePass = 1;

int OnInit()
{
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
}

void OnTick()
{
   // Deliberately empty: this fixture must never place a trade.
}

double OnTester()
{
   return((double)SmokePass);
}
