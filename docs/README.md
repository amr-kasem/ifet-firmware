# Configuration Documentation

## Modbus RTU Configuration

| Parameter | Device 1 | Device 2 | Notes |
|-----------|----------|----------|-------|
| Port | `/dev/ttyACM0` | `/dev/ttyACM0` | Same |
| Baudrate | 9600 | 9600 | Same |
| Byte Size | 8 | 8 | Same |
| Parity | PARITY_NONE | PARITY_NONE | Same |
| Stop Bits | 1 | 1 | Same |
| Mode | MODE_RTU | MODE_RTU | Same |
| Clear Buffers Before Each Transaction | true | true | Same |
| Close Port After Each Call | true | true | Same |

<div style="page-break-after: always;"></div>

## Pin Configuration

### Device 1 (config1.json)

```mermaid
flowchart LR
    V1["Valve 1 - Pin 13"] --> R1["ACTIVE, POSITIVE, POSITIVE_TURBO"]
    V2["Valve 2 - Pin 35"] --> R2["ACTIVE, NEGATIVE, RELIEF, POSITIVE_RELEASE, NEGATIVE_TURBO_SLAVE"]
    V3["Valve 3 - Pin 31"] --> R3["ACTIVE, POSITIVE, NEGATIVE_RELEASE, RELIEF, POSITIVE_TURBO_SLAVE"]
    V4["Valve 4 - Pin 15"] --> R4["ACTIVE, NEGATIVE, NEGATIVE_TURBO"]
```

### Device 2 (config2.json)

```mermaid
flowchart LR
    V1_2["Valve 1 - Pin 13"] --> R1_2["ACTIVE, POSITIVE, POSITIVE_TURBO"]
    V2_2["Valve 2 - Pin 35"] --> R2_2["ACTIVE, NEGATIVE, POSITIVE_RELEASE, RELIEF, NEGATIVE_TURBO_SLAVE"]
    V3_2["Valve 3 - Pin 31"] --> R3_2["ACTIVE, POSITIVE, NEGATIVE_RELEASE, RELIEF, POSITIVE_TURBO_SLAVE"]
    V4_2["Valve 4 - Pin 15"] --> R4_2["ACTIVE, NEGATIVE, NEGATIVE_TURBO, POSITIVE_TURBO_SLAVE"]
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
