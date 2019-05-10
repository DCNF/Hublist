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

- DC++: [dcpp/FavoriteManager.cpp#l322](https://sourceforge.net/p/dcplusplus/code/ci/3c319ced/tree/dcpp/FavoriteManager.cpp#l322)
- AirDC++: [modules/HublistManager.cpp#L58](https://github.com/airdcpp/airgit/blob/9954da1c/airdcpp/airdcpp/modules/HublistManager.cpp#L58)
- EiskaltDC++: [dcpp/FavoriteManager.cpp#L255](https://github.com/eiskaltdcpp/eiskaltdcpp/blob/2b38b58e/dcpp/FavoriteManager.cpp#L255)
- FlyLinkDC: [windows/PublicHubsFrm.cpp#L56](https://github.com/pavel-pimenov/flylinkdc-r5xx/blob/24db5c75/windows/PublicHubsFrm.cpp#L56)


## Why some hubs are offline, and written on your hublist as online?

As I'm doing update weekly, and not every hour like other hublist, it's why this hublist doesn't have the very last accurate online/offline mode.<br>
Sadly It's not on on my top priority on the moment, to run/commit every hour a xml file. If you have automatic solution, do not hesitate to contact me, even using the bug tacker of this project.

## License

[GPLv2 or later](https://github.com/DCNF/Hublist/blob/master/LICENSE)
