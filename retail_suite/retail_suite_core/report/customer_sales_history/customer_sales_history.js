frappe.query_reports["Customer Sales History"] = {
	filters: [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
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
			fieldname: "customer",
			label: "Customer",
			fieldtype: "Link",
			options: "Customer",
		},
	],
};
