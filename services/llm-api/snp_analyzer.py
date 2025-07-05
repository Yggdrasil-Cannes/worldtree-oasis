#!/usr/bin/env python3
"""Genetic SNP analysis module for ROFL."""

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class SNPAnalyzer:
    """Analyze SNP data for genetic relatedness using PCA."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def parse_snp_data(self, snp_lines):
        """Parse SNP data in format: rsID position chromosome genotype"""
        snps = {}
        for line in snp_lines:
            if not line.strip() or line.startswith('#'):
                continue
                
            parts = line.strip().split()
            if len(parts) >= 4:
                rsid = parts[0]
                position = parts[1]
                chromosome = parts[2]
                genotype = parts[3].upper()
                
                # Store by rsID for easy matching between samples
                snps[rsid] = {
                    'position': position,
                    'chromosome': chromosome,
                    'genotype': genotype
                }
        
        return snps
    
    def encode_genotype(self, genotype):
        """
        Encode genotype to numerical value using additive model.
        AA, TT, CC, GG = 0 (homozygous reference)
        AT, AG, AC, etc. = 1 (heterozygous)
        Different homozygous = 2 (homozygous alternate)
        Missing/Invalid = -1
        """
        if len(genotype) != 2:
            return -1
        
        allele1, allele2 = genotype[0], genotype[1]
        
        # Check for missing data
        if '-' in genotype or 'N' in genotype:
            return -1
            
        # Homozygous - both alleles the same
        if allele1 == allele2:
            # We need reference allele info to properly code 0 vs 2
            # For now, use alphabetical ordering as proxy
            if genotype in ['AA', 'CC']:
                return 0
            else:  # GG, TT
                return 2
        else:
            # Heterozygous
            return 1
    
    def prepare_snp_matrix(self, user1_snps, user2_snps):
        """
        Prepare aligned SNP matrix for both users.
        Only includes SNPs present in both samples.
        """
        # Find common SNPs
        common_rsids = set(user1_snps.keys()) & set(user2_snps.keys())
        logger.info(f"Found {len(common_rsids)} common SNPs out of {len(user1_snps)} and {len(user2_snps)}")
        
        if len(common_rsids) < 1000:
            logger.warning("Very few common SNPs found. Results may be unreliable.")
        
        # Sort for consistent ordering
        common_rsids = sorted(list(common_rsids))
        
        # Create numerical arrays
        user1_encoded = []
        user2_encoded = []
        valid_positions = []
        
        for i, rsid in enumerate(common_rsids):
            enc1 = self.encode_genotype(user1_snps[rsid]['genotype'])
            enc2 = self.encode_genotype(user2_snps[rsid]['genotype'])
            
            # Skip if either has missing data
            if enc1 >= 0 and enc2 >= 0:
                user1_encoded.append(enc1)
                user2_encoded.append(enc2)
                valid_positions.append(i)
        
        logger.info(f"Using {len(valid_positions)} valid SNPs after filtering")
        
        return np.array(user1_encoded), np.array(user2_encoded), len(valid_positions)
    
    def calculate_ibs_similarity(self, user1_encoded, user2_encoded):
        """
        Calculate Identity-By-State (IBS) similarity.
        This is a simple measure of genetic similarity.
        """
        # IBS0: No alleles shared (0 vs 2)
        # IBS1: One allele shared (0 vs 1, 1 vs 2)  
        # IBS2: Both alleles shared (same genotype)
        
        ibs0 = np.sum((user1_encoded == 0) & (user2_encoded == 2)) + \
               np.sum((user1_encoded == 2) & (user2_encoded == 0))
               
        ibs1 = np.sum((user1_encoded == 0) & (user2_encoded == 1)) + \
               np.sum((user1_encoded == 1) & (user2_encoded == 0)) + \
               np.sum((user1_encoded == 1) & (user2_encoded == 2)) + \
               np.sum((user1_encoded == 2) & (user2_encoded == 1))
               
        ibs2 = np.sum(user1_encoded == user2_encoded)
        
        total = len(user1_encoded)
        
        # IBS similarity score (weighted average)
        ibs_score = (ibs2 * 2 + ibs1 * 1) / (total * 2)
        
        return {
            'ibs0': int(ibs0),
            'ibs1': int(ibs1), 
            'ibs2': int(ibs2),
            'total_snps': int(total),
            'ibs_score': float(ibs_score)
        }
    
    def estimate_relationship(self, ibs_score, ibs2_ratio):
        """
        Estimate relationship based on IBS patterns.
        These are rough estimates based on expected sharing.
        """
        if ibs_score > 0.99:
            return "identical/twin", 0.99
        elif ibs_score > 0.85 and ibs2_ratio > 0.85:
            return "parent-child", 0.95
        elif ibs_score > 0.85 and ibs2_ratio > 0.75:
            return "full siblings", 0.90
        elif ibs_score > 0.70:
            return "grandparent-grandchild/aunt-uncle/half-siblings", 0.85
        elif ibs_score > 0.65:
            return "first cousins", 0.80
        elif ibs_score > 0.60:
            return "second cousins", 0.70
        elif ibs_score > 0.55:
            return "third cousins", 0.60
        else:
            return "distant relative or unrelated", 0.50
    
    def run_pca_analysis(self, user1_snps, user2_snps, n_components=10):
        """
        Run PCA analysis on SNP data to determine genetic similarity.
        """
        try:
            # Prepare data
            user1_encoded, user2_encoded, n_valid_snps = self.prepare_snp_matrix(user1_snps, user2_snps)
            
            if n_valid_snps < 100:
                raise ValueError("Insufficient valid SNPs for analysis")
            
            # Calculate IBS similarity
            ibs_results = self.calculate_ibs_similarity(user1_encoded, user2_encoded)
            ibs2_ratio = ibs_results['ibs2'] / ibs_results['total_snps']
            
            # Create combined matrix for PCA
            # Stack the two samples
            combined_data = np.vstack([user1_encoded, user2_encoded])
            
            # Apply PCA
            n_components_actual = min(n_components, 2, n_valid_snps)
            pca = PCA(n_components=n_components_actual)
            
            # Fit PCA on more samples if available, for now just these two
            # In production, you'd want a reference panel
            transformed = pca.fit_transform(combined_data.T).T
            
            # Calculate euclidean distance in PCA space
            pca_distance = np.linalg.norm(transformed[0] - transformed[1])
            
            # Estimate relationship
            relationship, confidence = self.estimate_relationship(
                ibs_results['ibs_score'], 
                ibs2_ratio
            )
            
            # Compile results
            results = {
                'status': 'success',
                'n_common_snps': n_valid_snps,
                'ibs_analysis': ibs_results,
                'ibs2_percentage': float(ibs2_ratio * 100),
                'relationship': relationship,
                'confidence': float(confidence),
                'pca_distance': float(pca_distance),
                'explained_variance_ratio': pca.explained_variance_ratio_.tolist() if hasattr(pca, 'explained_variance_ratio_') else None,
                'recommendations': self.get_recommendations(relationship, confidence)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"PCA analysis error: {e}")
            raise
    
    def get_recommendations(self, relationship, confidence):
        """Get recommendations based on relationship type."""
        recs = []
        
        if "parent-child" in relationship:
            recs.append("Very close genetic match consistent with parent-child relationship")
            recs.append("Consider sharing family history and medical information")
        elif "siblings" in relationship:
            recs.append("Close genetic match consistent with sibling relationship")
            recs.append("May share same parents - verify with family records")
        elif "cousin" in relationship:
            recs.append("Genetic match suggests cousin relationship")
            recs.append("Look for common grandparents or great-grandparents")
        elif "unrelated" in relationship:
            recs.append("No significant genetic relationship detected")
            recs.append("May still share very distant ancestry")
            
        if confidence < 0.8:
            recs.append("Consider additional genetic testing for higher confidence")
            
        return recs
