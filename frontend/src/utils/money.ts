/** Format an amount for display next to its currency code.
 *
 * Fixed to "en-US" rather than the browser locale on purpose: the POS runs
 * with an Arabic interface, and an Arabic locale would render amounts in
 * Arabic-Indic digits (٣٤٥٫٠٠) while every other number in the app - cart
 * totals, areas, box counts - stays in Latin digits. Money is the one thing
 * a salesperson reads back to a customer, so it follows the same digits as
 * the printed invoice instead of switching script mid-screen.
 *
 * Up to 3 decimals: LYD (this deployment's currency) has three.
 */
export function formatMoney(amount: number | null | undefined, currency?: string | null): string {
	const value = new Intl.NumberFormat("en-US", {
		minimumFractionDigits: 2,
		maximumFractionDigits: 3,
	}).format(amount ?? 0);
	return currency ? `${value} ${currency}` : value;
}
