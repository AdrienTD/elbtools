## About the engine

All games by ELB have more or less the same game files structure:

* GAME.Kpp
* 00GLOC.Kpp
* 01GLOC.Kpp
* ...
* LVL000/
  * LVL00.Kpp
  * 00LLOC00.Kpp
  * 01LLOC00.Kpp
  * ...
  * sssAS/
    * sssAS0.rws
    * sssAS1.rws
    * ...
    * SPEECH/
      * 0/
        * 0_sss0.RWS
        * 0_sss1.RWS
      * 1/
        * 1_sss0.RWS
        * 1_sss1.RWS
      * ...
* LVL001/
  * LVL01.Kpp
  * 00LLOC01.Kpp
  * 01LLOC01.Kpp
  * ...
  * pppAS/
    * ...
* ...

pp and sss depend on the platform the game is built for:

| Platform | Kpp | sssAS  |
|----------|-----|--------|
| Windows  | KWN | WINAS  |
| PS2      | KP2 | PS2AS  |