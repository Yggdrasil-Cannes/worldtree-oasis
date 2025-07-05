#!/usr/bin/env python3
"""Genetic SNP analysis module for ROFL (TEE-ready).

Designed for execution inside an **Oasis Trusted Execution Environment**, so
there are **no top-level side effects** (no CLI helper or `if __name__ ==`
guard). The public surface stays identical—only the PCA block is fixed and
cleaned.
"""

from __future__ import annotations

import logging
from typing import Iterable, Dict, List, Tuple, Any

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

AlleleEncoding = int


class SNPAnalyzer:
    """Analyse pair-wise SNP data for relatedness (IBS + optional PCA)."""

    # ------------------------------------------------------------------
    # Construction helper
    # ------------------------------------------------------------------

    def __init__(self, *, use_pca: bool = True, scaler: StandardScaler | None = None) -> None:
        self.use_pca = use_pca
        self.scaler = scaler or StandardScaler(with_mean=True, with_std=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_pca_analysis(
        self,
        user1_snps: Dict[str, Dict[str, str]],
        user2_snps: Dict[str, Dict[str, str]],
        *,
        n_components: int = 10,
    ) -> Dict[str, Any]:
        """Full analysis pipeline. Called by the enclave host."""
        # 1. Align & encode
        v1, v2, n_valid = self._prepare_snp_matrix(user1_snps, user2_snps)
        if n_valid < 100:
            raise ValueError("Insufficient valid SNPs (<100) for analysis")

        # 2. IBS similarity
        ibs = self._calculate_ibs_similarity(v1, v2)
        ibs2_ratio = ibs["ibs2"] / ibs["total_snps"]

        # 3. Optional PCA
        pca_dist: float | None = None
        explained_var: List[float] | None = None
        if self.use_pca:
            data = np.vstack([v1, v2])               # shape: (2, N)
            data = self.scaler.fit_transform(data)   # centre + scale cols
            max_rank = min(data.shape)               # ≤ 2 with two samples
            n_comp = max(1, min(n_components, max_rank))
            pca = PCA(n_components=n_comp)
            proj = pca.fit_transform(data)           # shape: (2, n_comp)
            pca_dist = float(np.linalg.norm(proj[0] - proj[1]))
            explained_var = pca.explained_variance_ratio_.tolist()
            logger.debug("PCA distance = %.4f", pca_dist)

        # 4. Relationship heuristic
        relationship, confidence = self._estimate_relationship(ibs["ibs_score"], ibs2_ratio)

        return {
            "status": "success",
            "n_common_snps": n_valid,
            "ibs_analysis": ibs,
            "ibs2_percentage": ibs2_ratio * 100.0,
            "relationship": relationship,
            "confidence": confidence,
            "pca_distance": pca_dist,
            "explained_variance_ratio": explained_var,
            "recommendations": self._get_recommendations(relationship, confidence),
        }

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def parse_snp_data(lines: Iterable[str]) -> Dict[str, Dict[str, str]]:
        """Parse 23-and-Me style genotype lines into a dict keyed by rsID."""
        snps: Dict[str, Dict[str, str]] = {}
        for ln in lines:
            if not ln.strip() or ln.startswith("#"):
                continue
            parts = ln.strip().split()
            if len(parts) < 4:
                continue
            rsid, pos, chrom, gt = parts[:4]
            snps[rsid] = {"position": pos, "chromosome": chrom, "genotype": gt.upper()}
        return snps

    # ------------------------------------------------------------------
    # Internal helpers (encoding, alignment, IBS, rules)
    # ------------------------------------------------------------------

    @staticmethod
    def _encode_genotype(gt: str) -> AlleleEncoding:
        if len(gt) != 2 or "-" in gt or "N" in gt:
            return -1
        a1, a2 = gt
        if a1 == a2:
            return 0 if gt in {"AA", "CC"} else 2
        return 1

    def _prepare_snp_matrix(
        self,
        u1: Dict[str, Dict[str, str]],
        u2: Dict[str, Dict[str, str]],
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        common = sorted(set(u1) & set(u2))
        if len(common) < 1000:
            logger.warning("Only %d common SNPs – estimates may be noisy", len(common))
        v1, v2 = [], []
        for rsid in common:
            g1 = self._encode_genotype(u1[rsid]["genotype"])
            g2 = self._encode_genotype(u2[rsid]["genotype"])
            if g1 >= 0 and g2 >= 0:
                v1.append(g1)
                v2.append(g2)
        return np.array(v1, dtype=np.int8), np.array(v2, dtype=np.int8), len(v1)

    @staticmethod
    def _calculate_ibs_similarity(v1: np.ndarray, v2: np.ndarray) -> Dict[str, int | float]:
        ibs0 = int(np.sum((v1 == 0) & (v2 == 2)) + np.sum((v1 == 2) & (v2 == 0)))
        ibs1 = int(
            np.sum((v1 == 0) & (v2 == 1))
            + np.sum((v1 == 1) & (v2 == 0))
            + np.sum((v1 == 1) & (v2 == 2))
            + np.sum((v1 == 2) & (v2 == 1))
        )
        ibs2 = int(np.sum(v1 == v2))
        total = len(v1)
        ibs_score = (2 * ibs2 + ibs1) / (2 * total)
        return {"ibs0": ibs0, "ibs1": ibs1, "ibs2": ibs2, "total_snps": total, "ibs_score": ibs_score}

    @staticmethod
    def _estimate_relationship(score: float, ibs2_ratio: float) -> Tuple[str, float]:
        if score > 0.99:
            return "identical/twin", 0.99
        if score > 0.85 and ibs2_ratio > 0.85:
            return "parent-child", 0.95
        if score > 0.85 and ibs2_ratio > 0.75:
            return "full siblings", 0.90
        if score > 0.70:
            return "grandparent-grandchild/aunt-uncle/half-siblings", 0.85
        if score > 0.65:
            return "first cousins", 0.80
        if score > 0.60:
            return "second cousins", 0.70
        if score > 0.55:
            return "third cousins", 0.60
        return "distant relative or unrelated", 0.50

    @staticmethod
    def _get_recommendations(rel: str, conf: float) -> List[str]:
        recs: List[str] = []
        if "parent-child" in rel:
            recs += [
                "Very close genetic match consistent with parent-child relationship",
                "Consider sharing family history and medical information",
            ]
        elif "siblings" in rel:
            recs += [
                "Close genetic match consistent with sibling relationship",
                "May share same parents – verify with family records",
            ]
        elif "cousin" in rel:
            recs += [
                "Genetic match suggests cousin relationship",
                "Look for common grandparents or great-grandparents",
            ]
        elif "unrelated" in rel:
            recs += [
                "No significant genetic relationship detected",
                "May still share very distant ancestry",
            ]
        if conf < 0.8:
            recs.append("Consider additional genetic testing for higher confidence")
        return recs