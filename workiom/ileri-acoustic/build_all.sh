#!/bin/bash
cd "$(dirname "$0")"
for pass in 1 2; do
  for f in apps/ileri_a1_crm.py apps/ileri_a2_proje.py apps/ileri_a3_hesap.py apps/ileri_a4_uretim.py apps/ileri_a5_satinalma.py; do
    echo "######## PASS $pass  $f"
    python3 main.py build "$f"
  done
done
