# Hublist

## How to use hublist.py?

The pinger helps us having more accurate data of an hub. 

### With the pinger DCPing

Version 0.8.8 of dcping works with our script (`a6e91ec`).

```
$ python3 hublist.py "[folder_to_dcping]/dcping"
```

### Without the pinger

```
$ python3 hublist.py
```

### `DCPing`?

**DCPing** is an open-source pinger build on GitHub: https://github.com/direct-connect/go-dcpp/tree/master/cmd/dcping.  
You can have a functionnal version by [building its source](https://github.com/direct-connect/go-dcpp/tree/master/cmd/dcping#build).

## Which attribute is used?

- https://sourceforge.net/p/dcplusplus/code/ci/default/tree/dcpp/FavoriteManager.cpp#l322
- https://github.com/airdcpp/airgit/blob/master/airdcpp/airdcpp/modules/HublistManager.cpp#L58
- https://github.com/pavel-pimenov/flylinkdc-r5xx/blob/master/windows/PublicHubsFrm.cpp#L56

## License

[GPLv2 or later](https://github.com/DCNF/Hublist/blob/master/LICENSE)
