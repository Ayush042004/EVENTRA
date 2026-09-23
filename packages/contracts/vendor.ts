import { VendorCategory, VendorAssignmentStatus } from "./enums";

export interface Vendor {
  id: string;
  companyName: string;
  contactName: string;
  contactPhone: string;
  category: VendorCategory;
  hourlyRate: number;
  rating: number;
  available: boolean;
}

export interface VendorResponse {
  id: string;
  name: string;
  category: string;
  city: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
  maps_url?: string;
  base_cost?: number;
  rating?: number;
  review_count?: number;
  service_description?: string;
  status: string;
  source: string;
  source_id?: string;
  raw_category?: string;
  capabilities?: string[];
  classification_confidence?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ProviderDiscoveryRequest {
  category?: string;
  query?: string;
  location?: string;
  latitude?: number;
  longitude?: number;
  limit?: number;
  use_real_scraper?: boolean;
}

export interface ProviderDiscoveryResponse {
  event_id?: string;
  total_discovered: number;
  total_created: number;
  total_updated: number;
  source: string;
  query_used: string[];
  items: VendorResponse[];
}

export interface VendorAssignment {
  id: string;
  eventId: string;
  vendorId: string;
  taskId?: string;
  category?: string;
  status: VendorAssignmentStatus;
  agreedFee?: number;
  agreed_cost?: number;
  notes?: string;
  negotiation_status?: string;
  target_amount?: number;
  max_approved_amount?: number;
  quoted_amount?: number;
  currency?: string;
  coverage_start?: string;
  coverage_end?: string;
  provider_count?: number;
  advance_required?: boolean;
  approval_id?: string;
  is_simulation?: boolean;
}

export interface VendorAssignmentResponse {
  id: string;
  event_id: string;
  vendor_id: string;
  category: string;
  status: string;
  negotiation_status: string;
  agreed_cost?: number;
  target_amount?: number;
  max_approved_amount?: number;
  quoted_amount?: number;
  currency: string;
  coverage_start?: string;
  coverage_end?: string;
  provider_count: number;
  advance_required?: boolean;
  approval_id?: string;
  is_simulation: boolean;
  created_at?: string;
  updated_at?: string;
}

