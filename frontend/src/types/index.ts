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
	/** The item's own ERPNext stock UOM (e.g. "Nos", "Bag") - only relevant
	 * when `custom_area_per_box` is 0/unset, i.e. this item isn't priced or
	 * sold by the square meter. */
	stock_uom: string;
	price_per_sqm?: number | null;
	/** Set instead of price_per_sqm when the item isn't area-based - the
	 * Item Price in its own stock UOM. */
	price_per_uom?: number | null;
}

export type SupplySource = "Company Warehouse" | "Supplier";

/** Is this item priced/sold through the m²/box engine at all? Some items
 * (piece, bag, ...) aren't - see calculation_service.is_area_based_item. */
export function isAreaBasedItem(item: PosItem): boolean {
	return !!item.custom_area_per_box;
}

export interface CalculationPreview {
	boxes: number;
	area_per_box: number;
	delivered_area_sqm: number;
	price_per_sqm: number;
	rate_per_box: number;
	amount: number;
}

/** Preview shape for a non-area item - see api/calculation.ts previewSimpleRow. */
export interface SimpleCalculationPreview {
	qty: number;
	uom: string;
	rate: number;
	amount: number;
}

export interface CartLine {
	key: string;
	item: PosItem;
	is_area_based: boolean;
	/** Set when is_area_based is true. */
	required_area_sqm: number | null;
	/** Set when is_area_based is false - a plain quantity in the item's own UOM. */
	qty: number | null;
	supply_source: SupplySource;
	/** Required when supply_source is "Supplier" - no Supplier Availability
	 * Confirmation is needed to check out by default (Retail Suite Settings
	 * can turn that requirement back on). */
	supplier: string | null;
	calculation: CalculationPreview | SimpleCalculationPreview;
}

export interface CustomerRef {
	name: string;
	customer_name: string;
}

export interface SupplierRef {
	name: string;
	supplier_name: string;
}

export interface SessionContext {
	showroom: string | null;
	is_unrestricted: boolean;
	price_list: string;
	currency: string | null;
}
