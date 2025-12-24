# Pin Configuration

## Device 1 (config1.json)

```mermaid
flowchart LR
    subgraph Device1["Device 1 - Pin Configuration"]
        V1_1["Valve 1<br/>Pin: 13<br/>Address: 1"]
        V2_1["Valve 2<br/>Pin: 35<br/>Address: 2"]
        V3_1["Valve 3<br/>Pin: 31<br/>Address: 3"]
        V4_1["Valve 4<br/>Pin: 15<br/>Address: 4"]
        
        V1_1 --> R1_1["ACTIVE<br/>POSITIVE<br/>POSITIVE_TURBO"]
        V2_1 --> R2_1["ACTIVE<br/>NEGATIVE<br/>RELIEF<br/>POSITIVE_RELEASE<br/>NEGATIVE_TURBO_SLAVE"]
        V3_1 --> R3_1["ACTIVE<br/>POSITIVE<br/>NEGATIVE_RELEASE<br/>RELIEF<br/>POSITIVE_TURBO_SLAVE"]
        V4_1 --> R4_1["ACTIVE<br/>NEGATIVE<br/>NEGATIVE_TURBO"]
    end
```

## Device 2 (config2.json)

```mermaid
flowchart LR
    subgraph Device2["Device 2 - Pin Configuration"]
        V1_2["Valve 1<br/>Pin: 13<br/>Address: 1"]
        V2_2["Valve 2<br/>Pin: 35<br/>Address: 2"]
        V3_2["Valve 3<br/>Pin: 31<br/>Address: 3"]
        V4_2["Valve 4<br/>Pin: 15<br/>Address: 4"]
        
        V1_2 --> R1_2["ACTIVE<br/>POSITIVE<br/>POSITIVE_TURBO"]
        V2_2 --> R2_2["ACTIVE<br/>NEGATIVE<br/>POSITIVE_RELEASE<br/>RELIEF<br/>NEGATIVE_TURBO_SLAVE"]
        V3_2 --> R3_2["ACTIVE<br/>POSITIVE<br/>NEGATIVE_RELEASE<br/>RELIEF<br/>POSITIVE_TURBO_SLAVE"]
        V4_2 --> R4_2["ACTIVE<br/>NEGATIVE<br/>NEGATIVE_TURBO<br/>POSITIVE_TURBO_SLAVE"]
    end
```

## Pin Mapping Summary

| Valve | Device 1 Pin | Device 2 Pin | Difference |
|-------|--------------|--------------|------------|
| Valve 1 | 13 | 13 | Same |
| Valve 2 | 35 | 35 | Same |
| Valve 3 | 31 | 31 | Same |
| Valve 4 | 15 | 15 | Same |

## Role Differences

**Valve 4**: Device 2 has additional role `POSITIVE_TURBO_SLAVE` that Device 1 does not have.
