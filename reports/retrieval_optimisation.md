# RAGAssist — Retrieval Optimisation Study

## Executive Summary

This study evaluates the impact of text chunk size and overlap on semantic retrieval performance in RAGAssist.

Three chunking configurations were compared using the same document collection, embedding model, FAISS retrieval algorithm, and nine answerable evaluation questions.

The **larger-chunk configuration (800 characters, 150-character overlap)** achieved the highest measured ranking performance:

- **Mean Recall@1:** 0.8333
- **Mean Recall@3:** 1.0000
- **MRR@3:** 0.9444
- **Mean retrieval latency:** 10.29 ms

Compared with the original 500-character configuration, larger chunks increased Mean Recall@1 from 0.5556 to 0.8333 and MRR@3 from 0.8148 to 0.9444.

However, the larger configuration generated only two chunks from the source document. Consequently, retrieving up to three results included the entire indexed collection, limiting the significance of its perfect Recall@3.

The findings demonstrate improved ranking on the current evaluation dataset but do not establish that larger chunks will perform better across larger or more diverse document collections.

## 1. Objective

The objective of this experiment was to determine whether adjusting text chunk size and overlap could improve:

- Retrieval of relevant evidence in the highest-ranked result.
- Ranking of the first relevant passage.
- Coverage of labelled supporting evidence within the top three results.
- Query retrieval latency.
- The balance between chunk granularity, context preservation, and index size.

Particular attention was given to questions about remote-working eligibility, approval authority, and policy-review frequency, which exhibited weaker rankings in the initial evaluation.

## 2. Experimental Setup

### 2.1 System Configuration

| Component | Configuration |
|---|---|
| Source documents | Fictional remote-working policy |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| Embedding dimensions | 384 |
| Vector search | FAISS IndexFlatIP |
| Similarity measure | Inner product on normalized embeddings |
| Evaluation questions | 9 answerable questions |
| Retrieval limit | Up to 3 chunks |
| Relevance labels | Evidence-phrase matching |

Document content, embedding model, retrieval method, and evaluation questions were held constant across all three configurations.

Each configuration generated its own document chunks and separate in-memory FAISS index. The application's persisted FAISS index was not modified.

### 2.2 Chunking Configurations

| Configuration | Chunk size | Chunk overlap | Generated chunks |
|---|---:|---:|---:|
| Baseline | 500 | 100 | 3 |
| Smaller chunks | 300 | 50 | 4 |
| Larger chunks | 800 | 150 | 2 |

All chunk sizes and overlap values are measured in characters.

## 3. Evaluation Metrics

**Mean Recall@1** measures the average fraction of labelled relevant chunks retrieved at rank 1.

**Mean Recall@3** measures the average fraction of labelled relevant chunks recovered within the first three results.

**MRR@3** measures the mean reciprocal rank of the first relevant chunk, assigning higher scores when relevant evidence appears earlier.

**Mean retrieval latency** measures the time required to embed a question and search the in-memory FAISS index.

**Evidence coverage** records whether each evaluation question has at least one chunk containing its labelled evidence phrase.

These metrics assess retrieval behaviour independently of downstream LLM answer correctness.

## 4. Experimental Results

### 4.1 Aggregate Performance

| Metric | Baseline | Smaller chunks | Larger chunks |
|---|---:|---:|---:|
| Chunk size | 500 | 300 | 800 |
| Chunk overlap | 100 | 50 | 150 |
| Indexed chunks | 3 | 4 | 2 |
| Questions evaluated | 9 | 9 | 9 |
| Questions with labelled evidence | 9 | 9 | 9 |
| Questions without labelled evidence | 0 | 0 | 0 |
| Mean Recall@1 | 0.5556 | 0.5556 | **0.8333** |
| Mean Recall@3 | 1.0000 | 1.0000 | 1.0000 |
| MRR@3 | 0.8148 | 0.8148 | **0.9444** |
| Mean latency | 20.67 ms | 10.39 ms | 10.29 ms |

All configurations preserved detectable labelled evidence for all nine questions.

The larger-chunk configuration achieved the highest Mean Recall@1 and MRR@3.

### 4.2 Improvements Relative to Baseline

| Metric | Baseline | Larger chunks | Difference |
|---|---:|---:|---:|
| Mean Recall@1 | 0.5556 | 0.8333 | +0.2777 |
| Mean Recall@3 | 1.0000 | 1.0000 | No change |
| MRR@3 | 0.8148 | 0.9444 | +0.1296 |
| Indexed chunks | 3 | 2 | −1 chunk |

The larger-chunk configuration produced an approximately **27.77-percentage-point increase in Mean Recall@1** and a **0.1296 increase in MRR@3**.

These improvements were measured on the current nine-question dataset and should not be interpreted as generalised performance gains.

## 5. Question-Level Analysis

### 5.1 Comparison of First-Relevant-Result Ranking

| Question | Baseline rank | Smaller-chunk rank | Larger-chunk rank |
|---|---:|---:|---:|
| Q01 — Working abroad | 1 | 1 | 1 |
| Q02 — HR approval | 1 | 1 | 1 |
| Q03 — Core working hours | 1 | 1 | 1 |
| Q04 — Working days | 1 | 1 | 1 |
| Q05 — Equipment provision | 1 | 1 | 1 |
| Q06 — Remote-working eligibility | 2 | 2 | **1** |
| Q07 — Line-manager approval | 2 | 2 | **1** |
| Q08 — Policy-review frequency | 3 | 3 | **2** |
| Q09 — Personal-device restrictions | 1 | 1 | 1 |

The rank refers to the first retrieved chunk containing the labelled evidence phrase. It does not describe whether every relevant chunk appeared at that rank.

### 5.2 Remote-Working Eligibility — Q06

**Question:** When can employees request remote working?

The relevant evidence states that employees may request remote-working arrangements after completing three months of employment.

The baseline and smaller-chunk configurations returned the first relevant passage at rank 2, producing a reciprocal rank of 0.50.

The larger-chunk configuration placed the relevant evidence at rank 1, increasing the reciprocal rank to 1.00.

This suggests that the larger passage representation better matched the eligibility question in this evaluation.

### 5.3 Approval Authority — Q07

**Question:** Who approves ordinary remote-working requests?

The relevant policy states that requests must be approved by the employee's line manager.

Both the baseline and smaller-chunk configurations ranked this evidence second.

The larger-chunk configuration ranked it first.

This represents an improvement in evidence ranking for a question where the system must distinguish ordinary remote-working approval from the separate HR approval required for working abroad.

### 5.4 Policy-Review Frequency — Q08

**Question:** How often are remote-working arrangements reviewed?

The expected evidence specifies a review interval of six months.

The baseline and smaller-chunk configurations ranked the first relevant evidence at position 3, giving a reciprocal rank of approximately 0.3333.

The larger-chunk configuration improved this to position 2, giving a reciprocal rank of 0.50.

Although ranking improved, the relevant evidence did not become the highest-ranked result.

Q08 therefore remains a candidate for further investigation.

### 5.5 Core Working Hours — Q03 and Q04

Both questions achieved a reciprocal rank of 1.00 under all three configurations.

However, Recall@1 changed because the number of chunks containing the labelled evidence varied.

The baseline configuration placed the evidence phrase in two overlapping chunks and retrieved one of them at rank 1, producing Recall@1 = 0.50.

The smaller and larger configurations each had one labelled relevant chunk, which appeared at rank 1, producing Recall@1 = 1.00.

This illustrates an important limitation of chunk-level Recall@K: **changing chunk boundaries changes the number of labelled relevant chunks and therefore the metric denominator**.

Higher Recall@1 does not always mean a greater amount of distinct information was retrieved.

### 5.6 Working Abroad — Q01 and Q02

The baseline and larger-chunk configurations achieved Recall@1 = 1.00 for both questions.

The smaller-chunk configuration achieved Recall@1 = 0.50 because the labelled evidence appeared in two chunks, only one of which occupied rank 1.

Despite the lower Recall@1, the first result was relevant in both cases, and both labelled chunks appeared within the top three.

Thus, the smaller configuration did not lose the required evidence; its lower Recall@1 partly reflects duplication across overlapping chunks.

### 5.7 Equipment Provision — Q05

The baseline and smaller-chunk configurations achieved Recall@1 = 1.00.

The larger-chunk configuration achieved Recall@1 = 0.50 because the evidence phrase appeared in two chunks, with only one retrieved at rank 1.

The first result remained relevant, and both labelled chunks appeared within the available results.

This is another example of changes in evidence duplication affecting chunk-level recall scores.

## 6. Latency Analysis

| Configuration | Mean retrieval latency |
|---|---:|
| Baseline | 20.67 ms |
| Smaller chunks | 10.39 ms |
| Larger chunks | 10.29 ms |

The larger-chunk configuration recorded the lowest mean latency, closely followed by smaller chunks.

However, the measurements should be interpreted cautiously.

The baseline configuration included a comparatively slow Q02 retrieval of 73.93 ms, which influenced its average.

The configurations were evaluated sequentially using the same loaded embedding model. Runtime warm-up, model caching, and execution-order effects may therefore have affected the comparison.

Additionally, the indexed collections contained only two to four vectors, making differences in FAISS search cost relatively small.

The results do not establish that larger chunks are inherently faster.

A more reliable latency comparison would repeat each configuration multiple times, vary execution order, and report median and percentile latency alongside the mean.

The previously recorded retrieval baseline of 211.41 ms was produced during a separate evaluation run. It should not be directly compared with these measurements without controlling for warm-up and runtime conditions.

## 7. Key Findings

### Improved Ranking with Larger Chunks

The 800-character configuration improved Mean Recall@1 and MRR@3 relative to both alternatives.

It also moved the relevant evidence for remote-working eligibility and line-manager approval to rank 1, while improving policy-review evidence from rank 3 to rank 2.

### Smaller Chunks Did Not Improve Aggregate Ranking

The 300-character configuration generated more chunks but achieved the same aggregate Recall@1 and MRR@3 as the baseline.

It improved some individual Recall@1 scores while reducing others, largely because different amounts of overlapping evidence were labelled relevant.

### Labelled Evidence Was Available in Every Configuration

All nine evaluation questions had identifiable supporting evidence under each chunking configuration.

No evaluated configuration lost all detectable evidence for any question.

### Perfect Recall@3 Has Limited Discriminative Value

The baseline configuration contained three indexed chunks, meaning Top-3 retrieval returned the entire indexed collection.

The larger-chunk configuration contained only two chunks, so Top-3 retrieval also returned its entire collection.

The smaller configuration contained four chunks, making Top-3 retrieval a slightly more selective test.

Consequently, Recall@3 = 1.00 across all configurations is encouraging but does not demonstrate robust retrieval performance on a larger corpus.

### Chunk-Level Metrics Depend on Chunk Boundaries

Overlapping chunks can contain duplicate instances of the same evidence phrase.

Because the evaluation labels relevant chunks using phrase matching, changing chunk size or overlap changes the number of gold-labelled chunks.

This affects Recall@K independently of whether the correct answer-supporting information is present.

### Retrieval Optimisation Does Not Resolve All Answer Failures

The previous answer-quality evaluation identified incorrect abstentions on questions about working hours, working days, and policy-review frequency.

Supporting evidence was available within the retrieved passages for these questions.

Therefore, improving retrieval rankings alone cannot be assumed to resolve these failures. LLM generation and citation-validation behaviour require separate evaluation.

## 8. Limitations

1. **Small document collection:** The experiment used one fictional remote-working policy containing only two to four indexed chunks, depending on configuration.

2. **Limited evaluation set:** Nine answerable questions are insufficient to establish general retrieval performance.

3. **Non-independent relevance labels:** Relevant chunks were identified using evidence-phrase matching rather than comprehensive human-labelled passage relevance.

4. **Changing gold-label counts:** Different chunk boundaries produced different numbers of relevant chunks, complicating direct Recall@K comparisons.

5. **Low retrieval selectivity:** A retrieval limit of three returned the entire collection for two configurations.

6. **Limited latency measurements:** Each question was timed during a single sequential comparison run without repeated trials or controlled warm-up.

7. **No end-to-end answer comparison:** This experiment measured retrieval but did not evaluate whether different chunk sizes improve LLM answer correctness or citation support.

8. **Potential context dilution:** Larger chunks contain more surrounding information, which may introduce irrelevant context in larger or more complex documents.

9. **No generalisation assessment:** Results may differ substantially on multi-document collections, longer PDFs, or documents containing conflicting information.

## 9. Recommended Configuration

**The 800-character chunk size with 150-character overlap is the strongest candidate for further testing based on the measured ranking metrics.**

It achieved the highest Mean Recall@1 and MRR@3 and improved rankings for the three questions targeted for investigation.

However, the experiment does not provide sufficient evidence to replace the existing production baseline definitively.

Because the larger configuration reduces the indexed collection to only two chunks, its current advantage may depend heavily on the small size and structure of the evaluation document.

**Recommendation:** Retain the existing 500-character / 100-character configuration as the reference implementation while treating 800-character / 150-character chunking as the leading experimental candidate.

A final configuration decision should follow evaluation on a larger document collection where Top-3 retrieval does not return most or all indexed chunks.

## 10. Recommended Improvements

### Expand the Document Corpus

Evaluate multiple documents containing different structures, topics, and lengths. Include cases where relevant evidence is surrounded by unrelated content.

### Strengthen Relevance Labelling

Introduce manually reviewed relevance judgements to identify evidence semantically, rather than relying only on exact phrase occurrences.

### Compare Evidence Retrieval Across Configurations

Evaluate whether the required answer-supporting information appears within the retrieved context, independently of how many overlapping chunks contain a particular phrase.

### Evaluate End-to-End Answer Quality

Run the same question set through the complete RAG pipeline for each candidate configuration.

Compare factual correctness, citation support, unnecessary abstentions, and response latency.

### Investigate Ranking Improvements

Examine whether the larger-chunk configuration continues to improve eligibility, approval-authority, and review-frequency retrieval when the document collection grows.

### Improve Performance Benchmarking

Repeat retrieval measurements with controlled warm-up and multiple runs, reporting median and percentile latency.

## 11. Conclusion

The retrieval optimisation experiment found that larger text chunks improved ranking metrics on the current RAGAssist evaluation dataset.

The 800-character / 150-character-overlap configuration achieved Mean Recall@1 of 0.8333 and MRR@3 of 0.9444, compared with 0.5556 and 0.8148 respectively for the baseline.

The main improvements involved remote-working eligibility, line-manager approval, and policy-review frequency.

Nevertheless, the experiment's small document collection, changing chunk-level relevance labels, and low Top-3 retrieval selectivity limit the generalisability of these results.

The larger-chunk configuration is therefore recommended for further evaluation rather than immediate adoption as the default.

These findings establish a reproducible experimental baseline and provide evidence-based priorities for improving RAGAssist's retrieval and answer-generation reliability.