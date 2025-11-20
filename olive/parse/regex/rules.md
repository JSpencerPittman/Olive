# TODO
## Thompson's
### Supported Special Operations
- Concatenation (no symbol)
- Or: `|`
- Optional: `?`
- At least one: `+`
- Any number: `*`

All operations will be of the form `( T1 T2 ... ) #OPERATION#`. 

### Preprocessing
Prior to processing the original rule is encapsulated in parentheses making concatenation the default operation.
```
SYMBOL := T1 T2 ...
# Becomes
SYMBOL := ( T1 T2 ... )
```

## Rules
### Special Expressions
| Character | Purpose | Alternative |
| ---- | ---- | --- |
| ` ` | Separate Tokens | `<space>` |
