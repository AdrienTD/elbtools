XXL Editor Preview 2
AdrienTD

With the XXL editor you can explore and modify the KWN files from the
Asterix XXL series as well as any games from Etranges Libellules using
the Kal engine.

Note that this is only a (pre-alpha) preview/demo, not everything works yet
and there might be a lot of bugs, but hopefully it will be improved over
the time.

Quick start:

- First, go to "Tools > Settings" in the menu and set the paths to the
  GameModule.elb files patched with Ipatix's patcher.

- Then, select the game version (XXL1, XXL2, OG) of the KWN files
  you want to open.

- Finally, open a KWN file by clicking "File > Open" or by drap-dropping the
  KWN file in the editor's window.

- You should then see the file appear in the tree at the left.
  Expand it to look at the chunks that the file contains.
  Click a chunk to display it at the right of the window.

  If for example you go to Level/Sector > Dictionaries >
  CTextureDictionary > 0, you can see the textures.

- Click "Hex" at the bottom to look at the bytes of the chunk, and
  click "Normal" to go back to an appropriate viewer/editor for the chunk.

- If you did some changes to a chunk and then select another chunk,
  the program will ask if you want to keep the changes. This will
  only save the changes in RAM memory, not on the KWN file!
  Say Yes to keep the changes.
  If you want to revert your changes, simply say No.

- When you're done with modding, click "File > Save LVL/LOC/STR" to
  save the corresponding file.

What the editor can do:
- View, export and edit textures in CTextureDictionary
- View and export Geometries to OBJ format
- View and edit localization text (CLocManager in GLOC.K* file)
- View the scene with its nodes and grounds/collision
- Export grounds/collision to OBJ format

Games supported:
- Asterix & Obelix XXL1
- Asterix & Obelix XXL2
- Arthur and the Invisibles
- Asterix at the Olympic Games

Current problems/limits:
- The PC versions of XXL1 and XXL2 have DRM/copy protection which replaces
  the header of the LVL file with random bytes, thus the editor won't be able
  to load them, as the editor needs the header to locate all the different
  objects stored in the LVL file (except for LVL00, which is not encrypted).
  But unecrypted headers for the LVL files can be found inside a cracked/patched
  executable of the game, so you can fix a LVL file by finding its header in the
  EXE and then copy it and paste it over the encrypted header in the LVL file.
  Olympic Games, the demo of XXL2, as well as console versions of the games are
  not affected.
  Preview 2 of the XXL editor fixed this problem by detecting encrypted
  headers and automatically finding the decrypted version in the game's
  executable (GameModule.elb). Saving a LVL with encrypted header will
  keep its encrypted header, so that the game can load it.

- Saving LVL files in XXL1 is OK but not for XXL2 and OG right now, because
  the newer games added new things in the format that I'm still looking at.
  As for STR, GLOC and LLOC files, saving works fine for all games.
  GAME.K* files can't be saved, because there is no point in editing them
  right now, but I will add support for that in the future.

- The editor was mainly made to work with the PC versions of the games (KWN files).
  It should still be able to load KP2/KGC/... files from consoles, but certain things
  might not work, like textures and geometries (because they use different formats
  optimized for consoles). However, ground collision, the scene viewer (without
  3D models) and the text editor might still work (at least for XXL1).
  (The text editor doesn't work in the PS2 version of XXL1, but does in GCN.)

Scene viewer
------------------

You can explore the scene and collision of a level and see the scene graph there.
To do it, open a LVL and/or a STR file and go to Tools > Scene viewer.

At the right is the 3D view of the scene.
Click and move the mouse there to rotate the camera.
Use the arrow or WASD/ZQSD keys to move the camera.
Right-click for some settings (wireframe, show/hide nodes and grounds).

At the left is the scene graph/tree.
Double-click an object there to move the camera to this object.

Geometry viewer
------------------

You can view a 3D model / geometry individually by opening a chunk inside the
"Geometry" group of a LVL or STR file.
Similarly to the scene viewer, use the arrow or WASD keys to move the camera,
and the mouse to rotate it.
Do a right-click on the viewer to get a menu of settings:
 - Use Wireframe to only draw the edges of the model's faces.
 - Use "Show connected geometries" to display other geometries
   connected to the current one (for example Asterix's model is separated in
   2/3 geometries, use this function to make all 3 appear in the same view.)
 - Use "Previous/Next costume" to show another "subgeometry". This is used
   in XXL1 for Asterix and Obelix's costumes.
 - Click "Save OBJ" to export the model in OBJ format.
   If "Show connected geometries" is enabled, then it will export all the 
   geometries in the view. 

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
