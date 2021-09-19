The files in the parent prop34 folder are files that are used by the THYME project.
Most of them were pre-existing xml files that have had adjustments made to them. (As opposed to completely
new xml files-- the bulk of completely new xml files were automatically generated via a csv file and a script,
and they can be found on github at propbank/propbank-development/thyme-files/non-overlap.)

The files in the sub-folder called spatial_thyme_shared are files that are used by both the THYME project and the
SpatialAMR project. 

How these files were created:
- start with the proposed34 version of the xml file from github propbank/propbank-development proposed34 branch
- add new rolesets from THYME (also in proposed34 format)
- make adjustments to any pre-existing rolesets (role changes, alias updates, new examples, new example names, etc.)
- delete old rolesets that are no longer in use (this only happens in cases where 2 rolesets are merged together.)

These files should be the final and most up to date version out of all of the various repositories. Choose these over 
other versions.

They have not been validated yet-- that still needs to be done. 
- example token numbering may need checking as well.