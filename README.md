# Hublist

## How to use hublist.py?

This hublist uses data from different XML / XML.BZ2 hubslist

### With the pinger DCPing

#### `DCPing`?

**DCPing** is an open-source pinger build on GitHub: https://github.com/direct-connect/go-dcpp/tree/master/cmd/dcping.  
You can have a functionnal version by [building its source](https://github.com/direct-connect/go-dcpp/tree/master/cmd/dcping#build).


The pinger helps us having more accurate data of an hub.

Version [v0.20.0](https://github.com/direct-connect/go-dcpp/tree/v0.20.0) of DCPing is compatible with this script.

```
$ python3 hublist.py "[folder_to_dcping]/dcping"
```

### Without the pinger

```
$ python3 hublist.py
```

## Which attribute is used?

- DC++: https://sourceforge.net/p/dcplusplus/code/ci/default/tree/dcpp/FavoriteManager.cpp#l322
- AirDC++: https://github.com/airdcpp/airgit/blob/master/airdcpp/airdcpp/modules/HublistManager.cpp#L58
- EiskaltDC++: https://github.com/eiskaltdcpp/eiskaltdcpp/blob/master/eiskaltdcpp-gtk/src/publichubs.cc#L46
- FlyLinkDC: https://github.com/pavel-pimenov/flylinkdc-r5xx/blob/master/windows/PublicHubsFrm.cpp#L56

## Why some hubs are offline, and written on your hublist as online?

As I'm doing update weekly, and not every hour like other hublist, it's why this hublist doesn't have the very last accurate online/offline mode.<br>
Sadly It's not on on my top priority on the moment, to run/commit every hour a xml file. If you have automatic solution, do not hesitate to contact me, even using the bug tacker of this project.

## License

[GPLv2 or later](https://github.com/DCNF/Hublist/blob/master/LICENSE)
