# schema_coverage results

Required (16): signal_array, channel_names, channel_units, sampling_rate_hz, n_channels, duration_sec, montage_system, reference_scheme, annotation_intervals, annotation_vocabulary, provenance, subject_id, subject_age, subject_sex, recording_datetime, filter_settings

Optional (5): channel_types, channel_positions_3d, power_line_frequency, institution, task

A field is optional if it is never or rare in two or more corpora.

| field | TUH_EEG | CHB-MIT | Sleep-EDF | BIDS-EEG | TUAR | decision |
| --- | --- | --- | --- | --- | --- | --- |
| signal_array | always | always | always | always | always | required |
| channel_names | always | always | always | always | always | required |
| channel_units | always | always | always | always | always | required |
| channel_types | rare | rare | often | always | rare | optional |
| sampling_rate_hz | always | always | always | always | always | required |
| n_channels | always | always | always | always | always | required |
| duration_sec | always | always | always | always | always | required |
| montage_system | often | always | always | often | often | required |
| reference_scheme | often | always | always | always | often | required |
| annotation_intervals | often | often | always | always | always | required |
| annotation_vocabulary | often | often | always | always | always | required |
| provenance | always | always | always | always | always | required |
| subject_id | always | always | always | always | always | required |
| subject_age | often | often | always | often | often | required |
| subject_sex | often | often | always | often | often | required |
| channel_positions_3d | never | never | never | often | never | optional |
| power_line_frequency | never | never | never | always | never | optional |
| recording_datetime | always | always | always | often | always | required |
| institution | rare | never | never | often | rare | optional |
| task | never | never | never | always | never | optional |
| filter_settings | often | rare | often | often | often | required |
