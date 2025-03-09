import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.cluster import SpectralClustering, KMeans, AgglomerativeClustering
from tasks.utils import preprocess
from sklearn.metrics import silhouette_score, silhouette_samples
import os.path
import numpy as np
from tasks.utils import get_material_id, get_clusters_range
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster

# + tags=["parameters"]
upstream = ["preprocessing"]
product = None
cluster_method = None
# -

print(cluster_method)

Path(product["nb"]).parent.mkdir(parents=True, exist_ok=True)
Path(product["data"]).mkdir(parents=True, exist_ok=True)


def cluster_kmeans(tag, df, columns_weights=None, alg="lloyd", clusters=[  3, 4]):
    silhouette_scores = []    
    range_n_clusters = []
    PARAM = []
    cluster_size = []
    for _c in clusters:
        PARAM.append({"n_clusters": _c} )
    X = preprocess(df,columns_weights=columns_weights)
    for param in PARAM:
        try:
            score = -1
            nclusters = -1
            clustering = KMeans(**param, algorithm=alg).fit(X)
            if all(x == clustering.labels_[0] for x in clustering.labels_):
                continue
            # Check for singletons (clusters with just one point)
            unique_labels, label_counts = np.unique(
                clustering.labels_, return_counts=True)            
            if any(count == 1 for count in label_counts):  # penalize if any cluster has only one point
                score = silhouette_score(X, clustering.labels_)   
            else:                   
                score = silhouette_score(X, clustering.labels_)
            nclusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
            silhouette_scores.append(score)    
            range_n_clusters.append(nclusters)
            cluster_size.append(param["n_clusters"])
        except Exception as err:
            print(param, err)           
            pass 
        

    # Plotting elbow curve and silhouette scores in subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))  # Adjust width and height as needed

    # Plotting silhouette scores
    ax2.plot(range_n_clusters, silhouette_scores, marker='o', linestyle='', color='g')
    ax2.set_xlabel('Number of Clusters')
    ax2.set_ylabel('Silhouette Score')
    ax2.set_title('[{}] Silhouette Score for Optimal Number of Clusters'.format(tag))
    ax2.set_xticks(range_n_clusters)
    ax2.grid(True)

    ax1.plot(cluster_size, silhouette_scores, marker='o', linestyle='', color='g')
    ax1.set_xlabel('Cluster size')
    ax1.set_ylabel('Silhouette Score')
    ax1.set_title('[{}] Silhouette Score for Optimal Number of Clusters'.format(tag))
    ax1.set_xticks(cluster_size)
    ax1.grid(True)


    # Find the optimal number of clusters based on silhouette score
    optimal_idx = silhouette_scores.index(max(silhouette_scores))
    optimal_params = PARAM[optimal_idx]
    print("optimal params",optimal_params)
    model = KMeans(**optimal_params).fit(X)
    sample_silhouette_values = silhouette_samples(X, model.labels_)
    print("Cluster labels (by number of clusters):", model.labels_)

    plt.tight_layout()
    plt.show() 

    return model, model.labels_ ,optimal_params, max(silhouette_scores), sample_silhouette_values


def cluster_spectral(tag, df, columns_weights=None, affinity="nearest_neighbors", clusters=[3, 5]):
    print(clusters)
    silhouette_scores = []    
    range_n_clusters = []
    PARAM = []
    cluster_size = []
    for _c in clusters:
        PARAM.append({"n_clusters": _c } )
    # they are already preprocessed
    # X = preprocess(df,columns_weights=columns_weights)
    X = df.drop(columns=[get_material_id()])
    for param in PARAM:
        try:
            score = -1
            nclusters = -1
            clustering = SpectralClustering(**param, affinity=affinity).fit(X)
            if all(x == clustering.labels_[0] for x in clustering.labels_):
                continue
            # Check for singletons (clusters with just one point)
            unique_labels, label_counts = np.unique(clustering.labels_, 
                                                    return_counts=True)
            if any(count == 1 for count in label_counts):  # Skip if any cluster has only one point
                score = silhouette_score(X, clustering.labels_)   
            else:                    
                score = silhouette_score(X, clustering.labels_)
            nclusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
            silhouette_scores.append(score)    
            range_n_clusters.append(nclusters)
            cluster_size.append(param["n_clusters"])
        except Exception as err:
            # print(param,err)           
            pass 
        

    # Plotting elbow curve and silhouette scores in subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))  # Adjust width and height as needed

    # Plotting silhouette scores
    ax2.plot(range_n_clusters, silhouette_scores, marker='o', linestyle='', color='g')
    ax2.set_xlabel('Number of Clusters')
    ax2.set_ylabel('Silhouette Score')
    ax2.set_title('[{}] Silhouette Score for Optimal Number of Clusters'.format(tag))
    ax2.set_xticks(range_n_clusters)
    ax2.grid(True)

    ax1.plot(cluster_size, silhouette_scores, marker='o', linestyle='', color='g')
    ax1.set_xlabel('Cluster size')
    ax1.set_ylabel('Silhouette Score')
    ax1.set_title('[{}] Silhouette Score for Optimal Number of Clusters'.format(tag))
    ax1.set_xticks(cluster_size)
    ax1.grid(True)


    # Find the optimal number of clusters based on silhouette score
    optimal_idx = silhouette_scores.index(max(silhouette_scores))
    optimal_params = PARAM[optimal_idx]
    print("optimal params",optimal_params)
    model = SpectralClustering(**optimal_params).fit(X)
    sample_silhouette_values = silhouette_samples(X, model.labels_)
    print("Cluster labels (by number of clusters):", model.labels_)

    plt.tight_layout()
    plt.show() 

    return model, model.labels_ ,optimal_params, max(silhouette_scores), sample_silhouette_values


_cluster_options = {
    "spectral" :  ["nearest_neighbors","rbf"],
    "kmeans" : [ "lloyd", "elkan"],
    "agglomerative" : ["ward", "complete", "single"]
}
    

def cluster_agglomerative(tag, df, columns_weights, _linkage="ward", clusters = [ 3, 4, 5, 6, 7]):
    silhouette_scores = []    
    new_range_n_clusters = []
    X = preprocess(df, columns_weights=columns_weights)
    for n_clusters in clusters:
        clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage=_linkage).fit(X)
        # Check for singletons (clusters with just one point)
        unique_labels, label_counts = np.unique(clustering.labels_,
                                            return_counts=True)
        if any(count == 1 for count in label_counts):  # Skip if any cluster has only one point
            score = silhouette_score(X, clustering.labels_)   
        else: 
            score = silhouette_score(X, clustering.labels_)   
        silhouette_scores.append(score)
        new_range_n_clusters.append(n_clusters)

    # Plotting elbow curve and silhouette scores in subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))  # Adjust width and height as needed

    # Plotting silhouette scores
    ax2.plot(new_range_n_clusters, silhouette_scores, marker='o', linestyle='-', color='g')
    ax2.set_xlabel('Number of Clusters')
    ax2.set_ylabel('Silhouette Score')
    ax2.set_title('[{}] Silhouette Score for Optimal Number of Clusters ({})'.format(tag,_linkage))
    ax2.set_xticks(new_range_n_clusters)
    ax2.grid(True)

    # Find the optimal number of clusters based on silhouette score
    optimal_idx = silhouette_scores.index(max(silhouette_scores))
    optimal_n_clusters = clusters[optimal_idx]
    print(">>> optimal_n_clusters", optimal_n_clusters, type(optimal_n_clusters))
    #optimal_n_clusters = 6
    model =  AgglomerativeClustering(distance_threshold=0, n_clusters=None,linkage=_linkage).fit(X)
    # model =  AgglomerativeClustering(n_clusters=optimal_n_clusters).fit(X)
    Z = linkage(X, method=_linkage)
    cluster_labels = fcluster(Z, optimal_n_clusters, criterion='maxclust')
    
    sample_silhouette_values = silhouette_samples(X, cluster_labels)
    print("Cluster labels (by number of clusters):", cluster_labels)


    #ax1.set_title("[{}] Hierarchical Clustering Dendrogram ({})".format(tag, _linkage))
    # cut the dendrogram to achieve optimal number of clusters
    # plot_dendrogram(model, ax=ax1, labels=df["RM"].values, 
     #               truncate_mode="lastp", p=int(optimal_n_clusters))
    ax1.set_xlabel("Number of points in node (or index of point if no parenthesis).")
    # Adjust layout
    plt.tight_layout()
    plt.show() 
    return model, cluster_labels, {"n_clusters": optimal_n_clusters}, max(silhouette_scores), sample_silhouette_values    


def apply_cluster(tag, df, cluster_method = "spectral", df_stats = []):
    clusters_range = get_clusters_range(df.shape[0])
    print(clusters_range)
    for affinity in _cluster_options[cluster_method]:
        if cluster_method == "spectral":
            model, cluster_labels,optimal_params, silhouette_score, silhouette_samples_score = cluster_spectral(tag,df,None,affinity,clusters=clusters_range)
        elif cluster_method == "kmeans":
            model, cluster_labels,optimal_params, silhouette_score, silhouette_samples_score = cluster_kmeans(tag,df,None,affinity,clusters=clusters_range)
        elif cluster_method == "agglomerative":
            model, cluster_labels,optimal_params, silhouette_score, silhouette_samples_score = cluster_agglomerative(tag,df,None,affinity,clusters=clusters_range)            
        else:
            continue

        df_result = df[[get_material_id()]].copy() 
        df_result["tag"] = tag
        df_result["cluster_method"] = cluster_method
        df_result['cluster_label'] = cluster_labels  #clustering.labels_
        df_result['silhouette_samples'] = silhouette_samples_score
        df_result.to_excel(os.path.join(product["data"],"{}_{}_{}.xlsx".format(tag,cluster_method,affinity)),index=False,sheet_name="_labels")    
        df_stats.append({"dataset": tag,"model": os.path.basename(product["data"]),"method" : affinity, "silhouette_score" : silhouette_score, "nclusters" : len(set(cluster_labels)),"params" : optimal_params})
    return df_stats


df_stats = []

df = pd.read_excel(upstream["preprocessing"]["x"])
print(df.columns, df.shape)
df_stats = apply_cluster("x", df, cluster_method, df_stats)

pd.DataFrame(df_stats).to_excel(product["stats"], index=False)