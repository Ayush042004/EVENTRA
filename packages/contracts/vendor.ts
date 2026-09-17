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

export interface VendorAssignment {
  id: string;
  eventId: string;
  vendorId: string;
  taskId: string;
  status: VendorAssignmentStatus;
  agreedFee: number;
  notes?: string;
}
