frappe.query_reports["Supplier Delivery Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "showroom",
			label: "Showroom",
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "supplier",
			label: "Supplier",
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "status",
			label: "Status",
			fieldtype: "Select",
			options: "\nDraft\nConfirmed\nDelivered\nCancelled",
		},
	],
};
