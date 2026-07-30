export interface ApiEnvelope<T> {
	success: boolean;
	message: string;
	data: T | null;
	errors: string[];
}

export interface PosItem {
	item_code: string;
	item_name: string;
	image: string | null;
	brand: string | null;
	custom_product_type: string | null;
	custom_width: number | null;
	custom_height: number | null;
	custom_thickness: number | null;
	custom_finish: string | null;
	custom_color: string | null;
	custom_collection: string | null;
	custom_series: string | null;
	custom_area_per_box: number;
	custom_pieces_per_box: number | null;
	custom_featured_product: 0 | 1;
	custom_display_sequence: number | null;
	price_per_sqm?: number | null;
}

export type SupplySource = "Company Warehouse" | "Supplier";

export interface CalculationPreview {
	boxes: number;
	area_per_box: number;
	delivered_area_sqm: number;
	price_per_sqm: number;
	rate_per_box: number;
	amount: number;
}

export interface CartLine {
	key: string;
	item: PosItem;
	required_area_sqm: number;
	supply_source: SupplySource;
	calculation: CalculationPreview;
}

export interface CustomerRef {
	name: string;
	customer_name: string;
}

export interface SessionContext {
	showroom: string | null;
	is_unrestricted: boolean;
	price_list: string;
	currency: string | null;
}
