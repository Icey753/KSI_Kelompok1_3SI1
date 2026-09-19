---
type: "query"
date: "2026-09-19T06:20:44.716861+00:00"
question: "Hubungan Ascon-128 (library ascon) dan Ascon-AEAD128 (NIST SP 800-232)?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["Ascon-128 (ascon library)", "Ascon-AEAD128 (NIST SP 800-232, formerly Ascon-128a)", "Ascon variant caveat: AEAD128 (SP 800-232) vs Ascon-128 v1.2"]
---

# Q: Hubungan Ascon-128 (library ascon) dan Ascon-AEAD128 (NIST SP 800-232)?

## Answer

Expanded from original query via vocab: [ascon, aead, variant, caveat, library, standard, nist, backend]. Graph: satu edge langsung Ascon-128 (ascon library) --conceptually_related_to [AMBIGUOUS]-- Ascon-AEAD128 (NIST SP 800-232, formerly Ascon-128a). Ascon-128 (ascon library) --conceptually_related_to [AMBIGUOUS]--> Ascon variant caveat (Plan A) --references [EXTRACTED]--> Ascon-AEAD128. Graf tidak menyelesaikan ambiguitas; hanya README ascon-c yang menyebut AEAD128 dahulu bernama Ascon-128a.

## Outcome

- Signal: useful

## Source Nodes

- Ascon-128 (ascon library)
- Ascon-AEAD128 (NIST SP 800-232, formerly Ascon-128a)
- Ascon variant caveat: AEAD128 (SP 800-232) vs Ascon-128 v1.2