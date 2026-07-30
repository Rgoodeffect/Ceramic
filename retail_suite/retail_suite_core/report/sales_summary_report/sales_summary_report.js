frappe.query_reports["Sales Summary Report"] = {
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
			fieldname: "salesperson",
			label: "Salesperson",
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "customer",
			label: "Customer",
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "item_group",
			label: "Item Group",
			fieldtype: "Link",
			options: "Item Group",
		},
	],
};
