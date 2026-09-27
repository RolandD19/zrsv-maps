# zrsv-maps

Python code to deserialize ZERO Sievert's .bin (map/room) files into JSON and vice versa (serialize JSON into .bin) and some custom test forest maps.

# Instructions 

To convert map .bin file to JSON: `python bin2json.py <BIN file> <JSON output>`
- e.g., `python bin2json.py r_b_forest_layout.bin r_b_forest_layout.json`

To convert JSON to a map .bin file: `python json2bin.py <JSON file> <new BIN file>`
- e.g., `python json2bin.py r_b_forest_layout.json r_b_forest_layout.bin`

Make sure to make backups if you overwrite any original .bin files. Map .bin files may be found in the game's root folder, e.g., `Program Files (x86)/Steam/steamapps/common/ZERO Sievert`.

The code has been tested with Python 3.9.16 under CYGWIN.

All .bin files of ZERO Sievert 1.3.3 have been successfully tested/compared  (using the `cmp` CYGWIN/Linux program).

ChatGPT was used to help generate the Python code.

# Additional modifications

To suppress some other map generation objects, via UTMT (UnderTaleModTool) and v1.3.3's `data.win` file:

## Suppress NPCs

In `gml_Object_obj_map_generator_Alarm_2`, line 2879, change:
`var _amount = 12` to `var _amount = 0` - This will suppress NPC generation

Or if you want to apply it just to the forest map:
```
if (area == UnknownEnum.Value_1)
   `var _amount = 0
```
Note: This does not suppress mob generation (wolves, boars, and mutants).

## Suppress other objects

To suppress other objects in `gml_GlobalScript_scr_area_data` (forest map only):

In (blank) line 7377, insert:
`area_obj_total_amount[a] = 0;` // Suppresses RNG mobs and anomalies
- This resets the counter after it's accumulated.

Alternatively, one can just "comment" out the loop in lines 7375-6.
- Because UTMT removes comments, one can preserve original code by blocking it out, e.g.,:
```
x = 0
if (x == 1) {
 for (var ll = 0; ll < array_length_2d(area_obj, a); ll++)
        area_obj_total_amount[a] += area_obj_amount[a][ll];
}
```

For buildings, trees/rocks/decor (in forest map only), change lines 7451-7452: 
```
area_different_building[a] = array_length_2d(area_building_list, a);
area_decor_number[a] = 22000;
```
into:
```
area_different_building[a] = 0 // Suppress the various buildings
area_decor_number[a] = 0` // Suppresses rocks, trees, etc.
```

Or (to preserve the original code):

```
x = 0
if (x == 1) {
  area_different_building[a] = array_length_2d(area_building_list, a);
  area_decor_number[a] = 22000;
} else {
  area_different_building[a] = 0 // Suppress the various buildings
  area_decor_number[a] = 0` // Suppresses rocks, trees, etc.
}
```

To suppress water/pond generation, back in `gml_Object_obj_map_generator_Alarm_2` (line 658, change:

`if (area == UnknownEnum.Value_1)`

into:

`if (area == UnknownEnum.Value_1 && false)` to suppress to water generation loops.

# Example/test maps

To test these maps, better to implement the above patches and overwrite `r_b_forest_layout.bin` with one of the files below (but that's not fully necessary).
- The .bin files are located in the `bin/` folder.
- Their corresponding JSON files are in the `json/` folder.
- The JSON was generated via AI (ChatGPT).

These are all unpolished/proofs-of-concept. These are the more interesting ones:

`forest_compact_4x4_clustered_blocks.bin` -- A custom village (does not show in minimap)
`forest_cliff_maze_narrow.bin` -- A "maze" using cliff walls (does show in minimap)
`forest_fence_maze.bin` -- A maze using fences
`forest_quarry_compact_dense_enemies.bin` -- A quarry/arena populated with enemies
`forest_quarry_hunters_watchers.bin` -- Another quarry/area populated with enemies

Other test maps available in the `bin/` and `json/` folders.

# Creating maps yourself via AI

Because the above maps were generated as part of a long ChatGPT thread, I'm not fully sure what you would need to attach to AI for it to populate/generate your own maps (as JSON). At minimum, it suggests:
- The full forest JSON (not provided here), so it can learn many map components.
- Some of the above example JSONs.
- The `npc.json` file found in `ZS_vanilla/gamedata`.

After AI produces a JSON file, convert it into a .bin file and copy/overwrite `r_b_forest_layout.bin`.
