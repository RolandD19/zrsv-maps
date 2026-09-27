# zrsv-maps

Python code to deserialize ZERO Sievert's .bin (map/room) files into JSON and vice versa (serialize JSON into .bin) and some custom test forest maps.

# Instructions 

To convert map .bin file to JSON: `python bin2json.py <BIN input> <JSON output>`
- e.g., `python bin2json.py r_b_forest_layout.bin r_b_forest_layout.json`

To convert JSON to a map .bin file: `python json2bin.py <JSON file> <new BIN file>`
- e.g., `python json2bin.py r_b_forest_layout.json r_b_forest_layout.bin`

Make sure to make backups if you overwrite any original .bin files. Map .bin files may be found in the game's root folder, e.g., `Program Files (x86)/Steam/steamapps/common/ZERO Sievert`.

To suppress some other map generation objects, via UTMT (UnderTaleModTool):
1. In `gml_Object_obj_map_generator_Alarm_2`, line 2879 (of 1.3.3), change:
`var _amount = 12` to `var _amount = 0` - This will suppress NPC generation
   - Or if you want to apply it just to the forest map:
```
if (area == UnknownEnum.Value_1)
`var _amount = 0
```
   - Note: This does not suppress mob generation (wolves, boars, and mutants).
2. To suppress other decor in forest map only, in `gml_GlobalScript_scr_area_data`, 
change (lines 7451-7452): 
```
area_different_building[a] = array_length_2d(area_building_list, a);
area_decor_number[a] = 22000;
```
to:
```
area_different_building[a] = 0;
area_decor_number[a] = 0;
````

The code has been tested with Python 3.9.16 under CYGWIN.

All .bin files of ZERO Sievert 1.3.3 have been successfully tested/compared  (using the `cmp` CYGWIN/Linux program).

ChatGPT was used to help generate the Python code.
