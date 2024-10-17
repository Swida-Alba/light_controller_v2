
// to drive the assigned LD cycles, LED or stepper.
// run on an Arduino Uno
// Jan 17, 2022 by Kangrui Leng, krleng@pku.edu.cn
// if not connected to a food motor, please set motorDelay to 0

bool isSerialMonitor = 1;
const int 
    n = 2,
    shiftN = 2;
const int       
    pin[n] = { 13, 12 }, // n pins with n frequencies to blink
    pin_on = 10, // constant on in L, constant off in D
    pin_on_rev = 9,  // constant on in D, constant off in L
    pin_motor[2] = { 3, 2 }, // pin_motor[0] on <- L, pin_motor[1] on <- D.
    pinRead = A0,
    dayN = 60, //// MODIFY //// LD[][0:1] is LD0, for acclimation, LD[][2:3] is LD1, the proper start of LD cycles
    
    dayShift[shiftN] = { 2, 4 }, // the L of (x+1)-th day will be delayed  
    sectN = dayN * 2 + 2; // # of sections in LD sequences 
const double
    f[n] = { 2, 2 }, // in Hz
    dutyCycle[n] = { 1, 1 }; // used to calculate PW when PW is set to {0}.
double
    interval[n] = { 0 },
    PW[n] = { 0, 0 }; // in ms; if set to 0, PW will be calculated by duty cycle.
int sect_i = 0;
unsigned long 
    LD[3][sectN] = { 0 },
    shiftTime[shiftN] = { (8 * 60) * 60000, (8 * 60) * 60000 }, // in ms; x min * 60000 ms/min
    // shiftTime[2] = {10000,10000},
    motorDelay = 0, // in ms; waiting for the initialization of food motor.
    //            LD[2][sectN]   = {{ 15,720,720,720,720,720,720,720,720,720}, // in min, LD protocol
    //                              {  1,  0,  1,  0,  1,  0,  1,  0,  1,  0}, // 0 is dark, 1 is light
    //                              {  1,  1,  1,  1,  1,  0,  1,  0,  1,  0}  // another condition, usually motor~food
    //                             },
    t0[n] = { 0 },
    curr0[n] = { 0 },
    tp0[n] = { 0 },
    tp00[n] = { 0 },
    t_Light0 = 0,
    t_Light = 0,
    t_Dark0 = 0,
    t_Dark = 0,
    sect_timer = 0;

bool
    fpul[n] = { 0 },
    motorFlag = 0,
    LightInitialized = 0,
    DarkInitialized = 0;
unsigned long t = 0, tt = 0; // Serial monitor
unsigned long
    tPrintPul0 = 0,
    tPrintPul = 1,
    smpInterval = 10; // sample interval of analog read

double fx(unsigned long ti, unsigned long td)
{ // frequency f = f0 * fx; interval I = I0 / fx;
    double x = (double)ti / td; // varies in [0,1] as a time factor for normalization ;
    double y = (-cos(x * 2 * PI) + 1) / 2;
    y = 1;
    if (y < 0) y = 0;
    return y;
}

void FillLDSections() 
{
    // fill the LD[3][sectN] array to alternate between L and D
    for (int i = 0; i < sectN; i++) 
    {
        if (i % 2 == 0) // when i is even, it's L
        {
            LD[0][i] = 43200000; // 12 hours in ms
            LD[1][i] = 1; // SIGNAL I ON
            LD[2][i] = 1; // SIGNAL II ON
        }
        else // when i is odd, it's D
        {
            LD[0][i] = 43200000; // 12 hours in ms
            LD[1][i] = 0; // SIGNAL I OFF
            LD[2][i] = 0; // SIGNAL II OFF
        }
    }

    // apply the time shifts
    for (int i = 0; i < shiftN; i++)
    {
        LD[0][dayShift[i] * 2 + 1] += shiftTime[i];
    }

    // set the DD after LD 3
    for (int i = 8; i < sectN; i++) 
    {
        LD[1][i] = 0; // SIGNAL I OFF
        LD[2][i] = 0; // SIGNAL II OFF
    }

    // set the remaining time to the start of the D of LD 0
    LD[0][0] = (3 * 60 + 37) * 60000; // 3 hours and 37 minutes in ms
}

void ResetPulse(int i)
{
    fpul[i] = true;
    t0[i] = 0;
    curr0[i] = millis();
    tp00[i] = millis();
    tp0[i] = 0;
}

void printLightIntensity(int pinPrint)
{
    int lightIntensity = analogRead(pinRead);
    Serial.print(millis());
    Serial.print('\t');
    Serial.println(lightIntensity);
}

void setup()
{
    Serial.begin(9600);
    FillLDSections();
    // initialization
    pinMode(pinRead, INPUT);
    pinMode(pin_on, OUTPUT);
    pinMode(pin_on_rev, OUTPUT);
    pinMode(pin_motor[0], OUTPUT);
    pinMode(pin_motor[1], OUTPUT);
    digitalWrite(pin_on, LOW);
    digitalWrite(pin_on_rev, LOW);
    digitalWrite(pin_motor[0], LOW);
    digitalWrite(pin_motor[1], LOW);
    for (int i = 0; i < n; i++)
    {
        pinMode(pin[i], OUTPUT);
        digitalWrite(pin[i], LOW);
        interval[i] = 1000 / f[i];
        if (PW[i] == 0)
        {
            PW[i] = interval[i] * dutyCycle[i];
        }
    }
    // motor and food
    unsigned long motor_t = 0, motor_t0 = millis();
    while (motor_t < motorDelay)
    {
        motor_t = millis() - motor_t0;
    }
    // initialize section timer
    sect_timer = millis();
}

void loop()
{
    //  tt = micros() - t;
    //  Serial.println(tt,DEC);
    //  t = micros();
    
    // section timer
    if (millis() - sect_timer >= LD[0][sect_i])
    {
        sect_i++;
        sect_timer = millis();
        LightInitialized = false;
        DarkInitialized = false;
        if (isSerialMonitor) {Serial.print("Section "); Serial.println(sect_i);}
        if (sect_i >= sectN) // THE END
        {
            digitalWrite(pin_on, LOW);
            digitalWrite(pin_on_rev, HIGH);
            for (int i = 0; i < n; i++)
            {
                digitalWrite(pin[i], LOW);
            }
            while (true) delay(100); // THE END
        }
    }
    
    // motor and food
    if (LD[2][sect_i] == 0 && motorFlag == 1) // if food will be available in next section
    {
        digitalWrite(pin_motor[0], LOW);
        digitalWrite(pin_motor[1], HIGH);
        motorFlag = 0;
        if (isSerialMonitor) Serial.println("CH2 OFF");
    }
    else if (LD[2][sect_i] == 1 && motorFlag == 0)
    {
        digitalWrite(pin_motor[0], HIGH);
        digitalWrite(pin_motor[1], LOW);
        motorFlag = 1;
        if (isSerialMonitor) Serial.println("CH2 ON");
    }

//    if (millis() % smpInterval == 0)
//    {
//        printLightIntensity(pinRead);
//    }

    unsigned long td = LD[0][sect_i];
    if (LD[1][sect_i] == 1) // is in Light
    {
        // initialize Light
        if (!LightInitialized)
        {
            if (isSerialMonitor) Serial.println("initialize L");
            t_Light0 = millis();
            t_Light = 0;
            for (int i = 0; i < n; i++)
            {
                ResetPulse(i);
            }
            digitalWrite(pin_on, HIGH);
            digitalWrite(pin_on_rev, LOW);
            for (int i = 0; i < n; i++)
            {
                digitalWrite(pin[i], HIGH);
                curr0[i] = millis();
            }
            LightInitialized = true;
        }
        // pulsing
        for (int i = 0; i < n; i++)
        {
            if (t0[i] < interval[i] / fx(t_Light, td))
                t0[i] = millis() - curr0[i];
            else
            {
                digitalWrite(pin[i], HIGH);
                ResetPulse(i);
            }
            if (fpul[i])
            {
                if (tp0[i] < PW[i])
                {
                    tp0[i] = millis() - tp00[i];
                }
                else
                {
                    digitalWrite(pin[i], LOW);
                    fpul[i] = false;
                    tp0[i] = 0;
                }
            }
        } // pulsing end
    }
    else // is in Dark
    {
        // initialize Dark
        if (!DarkInitialized)
        {
            if (isSerialMonitor) Serial.println("initialize D");
            t_Dark0 = millis();
            t_Dark = 0;
            digitalWrite(pin_on, LOW);
            digitalWrite(pin_on_rev, HIGH);
            for (int i = 0; i < n; i++)
            {
                digitalWrite(pin[i], LOW);
            }
            DarkInitialized = true;
        }
    }
}
