export interface Product {
  id: string;
  title: string;
  category: string | null;
  price: number | null;
  image_url: string | null;
}

export interface SearchHit extends Product {
  score: number;
}

export interface SearchResponse {
  results: SearchHit[];
  page: number;
  top_k: number;
  total_matches: number;
  has_more: boolean;
  took_ms: number;
  cached: boolean;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface CategoriesResponse {
  categories: CategoryCount[];
}

export interface SearchOptions {
  query: string;
  top_k?: number;
  page?: number;
  category?: string;
}

export interface ImageSearchOptions {
  file: File;
  top_k?: number;
  page?: number;
  category?: string;
}
