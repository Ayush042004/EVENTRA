export interface ProcurementItem {
  id: string;
  eventId: string;
  itemName: string;
  quantity: number;
  estimatedCost: number;
  vendorId?: string;
  status: "DRAFT" | "PENDING_APPROVAL" | "ORDERED" | "RECEIVED" | "CANCELLED";
  notes?: string;
}
