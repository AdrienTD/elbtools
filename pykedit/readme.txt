XXL Editor Preview 1
AdrienTD

With the XXL editor you can explore and modify the KWN files from the
Asterix XXL series as well as any games from Etranges Libellules using
the Kal engine.

Note that this is only a (pre-alpha) preview/demo, not everything works yet
and there might be a lot of bugs, but hopefully it will be improved over
the time.

Quick start:

- First, click "Version" in the menubar and select the game (XXL1, XXL2, OG)
  you want to use.

- Then, open a KWN file by clicking "File > Open" or by drap-dropping the
  KWN file in the editor's window.

Supported classes:
 Dictionary: CTextureDictionary
 Geometries
 3D: CLocManager

 Nodes
 3D: Grounds

Texture editor
------------------

To edit the textures, open a LVL or STR KWN file, then go to:
Home > Level/Sector > Dictionaries > CTextureDictionary

You will then see a list of available textures.
Click a texture to show it on screen.
Click the "Replace texture" button to replace the selected texture with a picture file.
Click "Save dictionary" to save the dictionary in the editor's memory, then you will still
have to save the KWN file with "Save LVL/STR" to get the modified KWN file.

Text editor
------------------

To change the text of a game, open a LOC KWN file, then go to:
Home > Local > Game things > CLocManager

You will see a table with 3 columns: the first is the ID of the string if any,
the second is the string, and the third is the original string before your changes.
You can only change the second column by single-clicking it or by pressing SPACE.
