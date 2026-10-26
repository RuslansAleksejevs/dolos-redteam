# Model and weight audit

Exact targets (zero-based module identifiers):

- `model.layers.7.self_attn.v_proj.bias`: shape [256], dtype torch.float32, donor FP32 SHA256 `8f3f5a735bcf53d9c1c1de26105b7578108af08b942506d2fabe85d59e34fb62`.
- `model.layers.7.self_attn.v_proj.weight`: shape [256, 1536], dtype torch.float32, donor FP32 SHA256 `4e96ef3d0a4f4f3d7bcbea0b2c0be22dcc956bb4f8ed47ca0c5add6252d96a0c`.
- `model.layers.15.self_attn.v_proj.bias`: shape [256], dtype torch.float32, donor FP32 SHA256 `923b1145dcaebd95c503e5c70a54bf8e4a4c5e88444f1901596667fe32096cd8`.
- `model.layers.15.self_attn.v_proj.weight`: shape [256, 1536], dtype torch.float32, donor FP32 SHA256 `47e085b4c32b8bb2d27d350ee907248e3661c24e84d262a6c6cc167ef2b47abc`.

Each donor is the pinned Dolos checkpoint tensor, including bias, with byte-identical hashes to the successful archived intervention. No approximation, head selection or other parameter is changed.

Every primary and engineering hybrid has a full state-dictionary fingerprint in provenance; changed tensor IDs must equal exactly the target set. All non-target tensors match original Qwen, including tied aliases. Original recipient tensors are restored and the complete model fingerprint is rechecked after every variant. Qwen-to-Qwen copies were checked before either donor intervention. Independent KV caches are created per generation batch and discarded before another prompt or variant.

{
  "engineering": {
    "passed": true,
    "checks": {
      "Q": {
        "max_archived_logp_error": 4.267692565917969e-05,
        "contexts": 16
      },
      "Q_V7": {
        "max_archived_logp_error": 5.6028482504189014e-05,
        "contexts": 16,
        "share_gain_by_wording": [
          0.10577722774955678,
          0.11139897811594052
        ]
      },
      "Q_V15": {
        "max_archived_logp_error": 5.245208740234375e-05,
        "contexts": 16,
        "share_gain_by_wording": [
          0.04826852568387437,
          0.04228743934191041
        ]
      },
      "D": {
        "max_archived_logp_error": 3.5136938095092773e-05,
        "contexts": 16
      }
    },
    "scope": "Previously evaluated contexts; implementation replication only, not new confirmation."
  },
  "numerical_checks": [
    {
      "stage": "engineering",
      "variant": "Q",
      "identical_copy_logp_error": 0.0,
      "all_parameters_identical": true
    },
    {
      "stage": "engineering",
      "variant": "Q",
      "batch_single_logp_error": 1.0233372449874878e-05
    },
    {
      "stage": "engineering",
      "variant": "Q",
      "restore_logp_error": 0.0,
      "every_parameter_restored": true
    },
    {
      "stage": "engineering",
      "variant": "Q_V7",
      "batch_single_logp_error": 1.1514872312545776e-05
    },
    {
      "stage": "engineering",
      "variant": "Q_V7",
      "restore_logp_error": 0.0,
      "every_parameter_restored": true
    },
    {
      "stage": "engineering",
      "variant": "Q_V15",
      "batch_single_logp_error": 7.752329111099243e-06
    },
    {
      "stage": "engineering",
      "variant": "Q_V15",
      "restore_logp_error": 0.0,
      "every_parameter_restored": true
    },
    {
      "stage": "engineering",
      "variant": "Q_V7_V15",
      "batch_single_logp_error": 4.855915904045105e-06
    },
    {
      "stage": "engineering",
      "variant": "Q_V7_V15",
      "restore_logp_error": 0.0,
      "every_parameter_restored": true
    },
    {
      "stage": "engineering",
      "variant": "D",
      "batch_single_logp_error": 9.650364518165588e-06
    },
    {
      "stage": "engineering",
      "variant": "D",
      "restore_logp_error": 0.0,
      "every_parameter_restored": true
    },
    {
      "stage": "primary",
      "variant": "Q",
      "identical_copy_logp_error": 0.0,
      "all_parameters_identical": true
    },
    {
      "stage": "primary",
      "variant": "Q",
      "batch_single_logp_error": 6.248196586966515e-05
    },
    {
      "stage": "primary",
      "variant": "Q",
      "restore_logp_error": 0.0,
      "every_parameter_restored": true
    },
    {
      "stage": "primary",
      "variant": "Q_V7",
      "batch_single_logp_error": 7.260777056217194e-05
    },
    {
      "stage": "primary",
      "variant": "Q_V7",
      "restore_logp_error": 0.0,
      "every_parameter_restored": true
    },
    {
      "stage": "primary",
      "variant": "Q_V15",
      "batch_single_logp_error": 8.563511073589325e-05
    },
    {
      "stage": "primary",
      "variant": "Q_V15",
      "restore_logp_error": 0.0,
      "every_parameter_restored": true
    },
    {
      "stage": "primary",
      "variant": "Q_V7_V15",
      "batch_single_logp_error": 7.82255083322525e-05
    },
    {
      "stage": "primary",
      "variant": "Q_V7_V15",
      "restore_logp_error": 0.0,
      "every_parameter_restored": true
    },
    {
      "stage": "primary",
      "variant": "D",
      "batch_single_logp_error": 8.419156074523926e-07
    },
    {
      "stage": "primary",
      "variant": "D",
      "restore_logp_error": 0.0,
      "every_parameter_restored": true
    }
  ]
}