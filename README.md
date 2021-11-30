# Hublist

## How to use hublist.py?

This hublist uses data from different XML / XML.BZ2 hublist.  
If you set the location of DCPing pinger as an argument, it'll try to ping every hub listed in all hublist.  
It takes ~40 minutes to ping all differents lists of hubs.

### Running hublist.py with the pinger DCPing

#### `DCPing`?

**DCPing** is an open-source pinger build on GitHub: https://github.com/direct-connect/go-dcpp/tree/master/cmd/dcping.  
You can have a functionnal version by [building its source](https://github.com/direct-connect/go-dcpp/tree/master/cmd/dcping#build).


The pinger helps us having more accurate data of an hub.

Version [v0.26.0](https://github.com/direct-connect/go-dcpp/tree/v0.26.0) of DCPing is compatible with this script.

```
$ python3 hublist.py "[folder_to_dcping]/dcping"
```

### Running hublist.py alone

```
$ python3 hublist.py
```

## Which attribute is used in most-used DC clients?

- DC++: [dcpp/FavoriteManager.cpp#l322](https://sourceforge.net/p/dcplusplus/code/ci/66549d/tree/dcpp/FavoriteManager.cpp#l322)
- AirDC++: [modules/HublistManager.cpp#L58](https://github.com/airdcpp/airdcpp-windows/blob/c8e3dc4/airdcpp/airdcpp/modules/HublistManager.cpp#L58)
- EiskaltDC++: [dcpp/FavoriteManager.cpp#L255](https://github.com/eiskaltdcpp/eiskaltdcpp/blob/1d113ac/dcpp/FavoriteManager.cpp#L255)
- FlyLinkDC: [windows/PublicHubsFrm.cpp#L53](https://github.com/pavel-pimenov/flylinkdc-r6xx/blob/92da92a/windows/PublicHubsFrm.cpp#L53)

## Why some hubs are offline, and written on your hublist as online?

I'm doing update weekly, and not every hour like other hublist, it's why this hublist doesn't have the very last accurate online / offline mode.<br>
Sadly It's not on on my priority of the moment to run hublist.py / commit every hour a xml file. If you have an automatic solution in mind, do not hesitate to contact me by opening an issue!

## License

[GPLv2 or later](https://github.com/DCNF/Hublist/blob/master/LICENSE)
