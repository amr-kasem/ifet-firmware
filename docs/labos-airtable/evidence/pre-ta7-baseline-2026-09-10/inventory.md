
### IFET Projects  (4 LabOS-relevant fields)

| Airtable Field | Field ID | Type | Testing | Production | Dir | Runtime owner/consumer | Register |
|---|---|---|---|---|---|---|---|
| Product Type | `fldR3PaaTo9BIjmSO` | singleLineText | present | present | IGNORED | -- | BASELINE |
| Project Status Modified Time | `fld2bJ2UQUoWrlQSu` | lastModifiedTime | present | present | IGNORED | -- | BASELINE |
| IFET job number | `fldZa91p5KebdT6q2` | singleLineText | present | present | IN | mirror.py allowlist | BASELINE |
| Project name | `fldXOI9t0N8oP4FLy` | singleLineText | present | present | IN | mirror.py allowlist | BASELINE |

### Mock-Ups/Specimens  (5 LabOS-relevant fields)

| Airtable Field | Field ID | Type | Testing | Production | Dir | Runtime owner/consumer | Register |
|---|---|---|---|---|---|---|---|
| Height (Inches) | `fldw4wNgbNM4NP9dr` | number | present | present | IGNORED | -- | BASELINE |
| Specimen status | `fldKhsUYTaQPKGtJL` | singleSelect | present | present | IGNORED | -- | BASELINE |
| Width (Inches) | `fldvm1NAoIGLrFbd0` | number | present | present | IGNORED | -- | BASELINE |
| IFET Job Number | `fldyj3e89pH6QH2Pp` | multipleRecordLinks | present | present | IN | mirror.py allowlist | BASELINE |
| Mock-up/specimen name | `fldyprpxI76d6CIxo` | singleLineText | present | present | IN | mirror.py allowlist | BASELINE |

### Tests Protocols  (2 LabOS-relevant fields)

| Airtable Field | Field ID | Type | Testing | Production | Dir | Runtime owner/consumer | Register |
|---|---|---|---|---|---|---|---|
| Mock-Up | `fldSzN0fPvbWyOgPu` | multipleRecordLinks | present | present | IN | mirror.py allowlist | BASELINE |
| Protocol Name | `fldvf05KHbDSMjLrw` | singleLineText | present | present | IN | mirror.py allowlist | BASELINE |

### Protocol Sections  (18 LabOS-relevant fields)

| Airtable Field | Field ID | Type | Testing | Production | Dir | Runtime owner/consumer | Register |
|---|---|---|---|---|---|---|---|
| Impact Locations | `-` | number | absent | absent | IGNORED | -- | OMITTED |
| Result | `fld9AO8n6OosZ80mW` | singleSelect | present | present | IGNORED | -- | BASELINE |
| Status | `fldeprjn5dCWBhT0G` | singleSelect | present | present | IGNORED | -- | BASELINE |
| Testing Date | `fldj3JimASOrUTrCu` | date | present | present | IGNORED | -- | BASELINE |
| Value | `fld1YDj3d2UilU7m6` | singleLineText | present | present | IGNORED | -- | BASELINE |
| Applicability | `fldh3VS09fonTLHsS` | singleSelect | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Impact Velocity | `fldJNfUVyqQEFOVWx` | number | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Missile Type | `fld5Bs0aQXXeVso2y` | singleLineText | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Missile Weight | `fldmhdhonyyLcx4Ex` | number | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Required Option | `fldflOxCkAK1BkU9l` | singleLineText | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Required Unit | `fldTjNKeQe7oxxl33` | singleSelect | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Required Value | `fldpL2dyGzKj9xowY` | number | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Required Value Inward | `fld1wR9ojdmESax0m` | number | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Required Value Outward | `fld7GLStvnPnYJPpd` | number | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Requirement Code | `fld9Fzjj25ngrVIOB` | singleSelect | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Requirement Kind | `fldWGpL9gJh89wSK8` | singleSelect | present | absent | IN | mirror.py allowlist -> importer/requirements | APPLIED |
| Section Name | `fldN0th87JyevlzgU` | singleLineText | present | present | IN | mirror.py allowlist -> importer/requirements | BASELINE |
| Test Protocol | `fld3EtgBWkjqAXHGp` | multipleRecordLinks | present | present | IN | mirror.py allowlist -> importer/requirements | BASELINE |

### LabOS Raw Data Table  (41 LabOS-relevant fields)

| Airtable Field | Field ID | Type | Testing | Production | Dir | Runtime owner/consumer | Register |
|---|---|---|---|---|---|---|---|
| (delivery metadata) | `-` | - | absent | absent | LOCAL_ONLY | -- | PLANNED |
| ANSI Result | `-` | singleSelect | absent | absent | OUT | -- NONE -- | OMITTED |
| Airtable Mockup ID | `fldV0IzvUSnmlVKC3` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | BASELINE |
| Airtable Project ID | `fldgIIL715TrhyvKE` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py | BASELINE |
| Airtable Protocol ID | `fldVPHPXqlPGnBUSB` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py | BASELINE |
| Airtable Section ID | `fld0dex9BWVQzgRLS` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py | BASELINE |
| Attempt Number | `fldyQpMOaSdWzO7xR` | number | present | present | OUT | contract.FIELDS + mapping.py | BASELINE |
| Complete LabOS JSON Response | `fldeG1iA6TVWOSi0T` | multilineText | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | BASELINE |
| Correction Reason | `fldCh0DXyvROqZBaJ` | multilineText | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | BASELINE |
| Corrects Attempt ID | `fldV4ucQNEA0gYfMc` | singleLineText | present | absent | OUT | contract.FIELDS + mapping.py + envelope.py | APPLIED |
| Deflection Unit | `fldvZMcxhm9R9Lzg7` | singleLineText | present | present | OUT | contract.FIELDS + envelope.py | OMITTED |
| Deflection Value | `fldg21XOFDAKWvUZx` | number | present | present | OUT | contract.FIELDS + envelope.py | OMITTED |
| Excel File Link | `fldQAF1pExVQ9Xe6O` | url | present | present | OUT | contract.FIELDS + mapping.py | CONDITIONAL |
| Failure Notes | `-` | multilineText | absent | absent | OUT | -- NONE -- | OMITTED |
| Forced Entry Result | `-` | singleSelect | absent | absent | OUT | -- NONE -- | OMITTED |
| Impact Number | `fldk52wf0SO9zYDjB` | number | present | absent | OUT | contract.FIELDS + mapping.py | APPLIED |
| Impact Result | `flda24C2M2tWyXEdb` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py | BASELINE |
| LabOS Attempt ID | `fldDu6er95KG2pOrG` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py + envelope.py + client/sync (attachment) | BASELINE |
| LabOS Created At | `fldJYqMAdKP7v0zCU` | dateTime | present | present | OUT | contract.FIELDS + mapping.py | BASELINE |
| LabOS Photos | `fldsEfhtH9wXPAl1Y` | multipleAttachments | present | absent | OUT | contract.FIELDS + client/sync (attachment) | APPLIED |
| LabOS Report Link | `fldfewhrzgMnmAmU3` | url | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | CONDITIONAL |
| LabOS Test ID | `fldQWGjD0gQ4WwPbh` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py | BASELINE |
| LabOS Updated At | `fldmqwik5SKFHRVqd` | dateTime | present | present | OUT | contract.FIELDS + mapping.py | BASELINE |
| LabOS Verdict At | `fldqCkqAh7aTckxSR` | dateTime | present | absent | OUT | contract.FIELDS + mapping.py + envelope.py | APPLIED |
| LabOS Verdict By | `fldVedw9cOgne8UeX` | singleLineText | present | absent | OUT | contract.FIELDS + mapping.py + envelope.py | APPLIED |
| Max Pressure Achieved | `fldDZkfaE2T4bFZ8C` | number | present | present | OUT | contract.FIELDS + envelope.py | OMITTED |
| Measured Value | `fld0kER3p3ogmmP2L` | number | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | CONDITIONAL |
| Notes | `fldH5IvnQ0rL1xQRm` | multilineText | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | BASELINE |
| Operator Name | `fldNHIHKq4xPvYhzX` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py | BASELINE |
| Photos | `fld01SK9bnkTd9s29` | url | present | present | OUT | contract.FIELDS + mapping.py + client/sync (attachment) | CONDITIONAL |
| Retest Required | `fldBDTojy4Qk3LssD` | checkbox | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | BASELINE |
| Schema Version | `fldB8gHb2a5guxm7g` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | BASELINE |
| Test Date | `fld4hqC9SIQ9ll8mp` | dateTime | present | present | OUT | contract.FIELDS + envelope.py | BASELINE |
| Test Result | `fldAYKt62KMn9q7E6` | singleSelect | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | BASELINE |
| Test Status | `fldQ7u9PGz7S8Ngdb` | singleSelect | present | present | OUT | contract.FIELDS + envelope.py | BASELINE |
| Test Type | `fldu6lraAAKIAXIRQ` | singleSelect | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | BASELINE |
| Testing Continued | `fldCjb00kloRr9pGj` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py | BASELINE |
| Testing End Date | `fldTsjf78Y5fA85fz` | dateTime | present | absent | OUT | contract.FIELDS + mapping.py + envelope.py | APPLIED |
| Testing Start Date | `fldYU1BtWVuWv5DBV` | dateTime | present | absent | OUT | contract.FIELDS + mapping.py + envelope.py | APPLIED |
| Unit | `fld05iOwDiDtXA7b5` | singleLineText | present | present | OUT | contract.FIELDS + mapping.py + envelope.py | BASELINE |
| Raw Modified Time | `fldKxp708fktN57aH` | lastModifiedTime | present | present | READ_ONLY | -- | BASELINE |


### DISAGREEMENTS

- ABSENT LabOS Raw Data Table.(delivery metadata): not in Testing but register says PLANNED

Register rows outside the five tables: []
