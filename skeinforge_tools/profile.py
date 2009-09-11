"""
Profile is a script to set the craft types preference for the skeinforge chain.

Profile presents the user with a choice of the craft types in the craft_types folder.  The chosen craft type is used to
determine the craft type profile for the skeinforge chain.  The default craft type is extrusion.

The preference is the selection.  If you hit 'Save Preferences' the selection will be saved, if you hit 'Cancel' the selection
will not be saved.

To change the profile preference, in a shell in the profile folder type:
> python profile.py

An example of using profile from the python interpreter follows below.


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import profile
>>> profile.main()
This brings up the profile preference dialog.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import preferences


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getDisplayedPreferences():
	"Get the displayed preferences."
	return preferences.getDisplayedDialogFromConstructor( preferences.ProfilePreferences() )

def main():
	"Display the profile dialog."
	getDisplayedPreferences().root.mainloop()

if __name__ == "__main__":
	main()
