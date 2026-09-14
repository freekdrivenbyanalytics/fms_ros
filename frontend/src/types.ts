export type VisitStatus = "unassigned" | "assigned";

export interface GeoPoint {
  lat: number;
  lng: number;
}

export interface Region {
  id: number;
  name: string;
  geo_shape: GeoPoint[] | null;
}

export interface RegionCreateInput {
  name: string;
  geo_shape: GeoPoint[] | null;
}

export interface RegionUpdateInput {
  name: string;
  geo_shape: GeoPoint[] | null;
}

export interface Product {
  id: number;
  number: string;
  name: string;
}

export interface Customer {
  id: number;
  version: number | null;
  url: string | null;
  name: string;
  organization_number: string | null;
  global_location_number: number | null;
  supplier_number: number | null;
  customer_number: number | null;
  is_supplier: boolean | null;
  is_customer: boolean | null;
  is_inactive: boolean | null;
  email: string | null;
  invoice_email: string | null;
  overdue_notice_email: string | null;
  phone_number: string | null;
  phone_number_mobile: string | null;
  description: string | null;
  language: string | null;
  display_name: string | null;
  is_private_individual: boolean | null;
  single_customer_invoice: boolean | null;
  invoice_send_method: string | null;
  email_attachment_type: string | null;
  invoices_due_in: number | null;
  invoices_due_in_type: string | null;
  is_factoring: boolean | null;
  invoice_send_sms_notification: boolean | null;
  invoice_sms_notification_number: string | null;
  is_automatic_soft_reminder_enabled: boolean | null;
  is_automatic_reminder_enabled: boolean | null;
  is_automatic_notice_of_debt_collection_enabled: boolean | null;
  discount_percentage: number | null;
  website: string | null;
  account_manager: Record<string, unknown> | null;
  department: Record<string, unknown> | null;
  postal_address: Record<string, unknown> | null;
  physical_address: Record<string, unknown> | null;
  delivery_address: Record<string, unknown> | null;
  category1: Record<string, unknown> | null;
  category2: Record<string, unknown> | null;
  category3: Record<string, unknown> | null;
  currency: Record<string, unknown> | null;
  ledger_account: Record<string, unknown> | null;
  bank_account_presentation: unknown[] | null;
}

export interface CustomerLocation {
  id: number;
  address: string;
  latitude: number | null;
  longitude: number | null;
  coordinates_locked: boolean;
  customer: Customer;
  region: Region | null;
}

export interface CustomerLocationCoordinatesInput {
  latitude: number;
  longitude: number;
  coordinates_locked: boolean;
}

export interface ContractLine {
  id: number;
  contract_id: number;
  start_date: string;
  end_date: string | null;
  interval_days: number;
  duration_minutes: number;
  priority: number;
  customer_location: CustomerLocation;
  required_products: Product[];
}

export interface Contract {
  id: number;
  customer: Customer;
  lines: ContractLine[];
}

export interface ContractCreateInput {
  customer_id: number;
}

export interface ContractUpdateInput {
  customer_id: number;
}

export interface ContractLineCreateInput {
  customer_location_id: number;
  start_date: string;
  end_date: string | null;
  interval_days: number;
  duration_minutes: number;
  priority: number;
  required_product_ids: number[];
}

export interface ContractLineUpdateInput {
  customer_location_id: number;
  start_date: string;
  end_date: string | null;
  interval_days: number;
  duration_minutes: number;
  priority: number;
  required_product_ids: number[];
}

export type LunchType = "none" | "fixed" | "flexible";
export type DayType = "working" | "holiday" | "sick";

export interface EmployeeScheduleTemplate {
  id: number;
  employee_id: number;
  start_date: string;
  end_date: string | null;
  work_start: string;
  work_end: string;
  max_hours_per_day: number;
  lunch_type: LunchType;
  lunch_start: string | null;
  lunch_end: string | null;
  lunch_duration_minutes: number | null;
}

export interface EmployeeScheduleTemplateInput {
  start_date: string;
  end_date: string | null;
  work_start: string;
  work_end: string;
  max_hours_per_day: number;
  lunch_type: LunchType;
  lunch_start: string | null;
  lunch_end: string | null;
  lunch_duration_minutes: number | null;
}

export interface EmployeeScheduleDayOverride {
  id: number;
  employee_id: number;
  date: string;
  day_type: DayType;
  work_start: string | null;
  work_end: string | null;
  max_hours_per_day: number | null;
  overtime_minutes: number | null;
}

export interface EmployeeScheduleDayOverrideInput {
  date?: string;
  day_type: DayType;
  work_start: string | null;
  work_end: string | null;
  max_hours_per_day: number | null;
  overtime_minutes: number | null;
}

export interface EmployeeScheduleDayOverrideBulkInput {
  start_date: string;
  end_date: string;
  day_type: DayType;
}

export interface EmployeeRescoSyncResult {
  status: "synced" | "skipped" | "failed";
  detail: string | null;
}

export interface Employee {
  id: number;
  first_name: string;
  last_name: string;
  name: string;
  email: string | null;
  mobile_phone: string | null;
  latitude: number;
  longitude: number;
  regions: Region[];
  products: Product[];
  schedule_templates: EmployeeScheduleTemplate[];
  schedule_overrides: EmployeeScheduleDayOverride[];
  resco_sync: EmployeeRescoSyncResult | null;
}

export interface EmployeeCreateInput {
  first_name: string;
  last_name: string;
  email: string | null;
  mobile_phone: string | null;
  latitude: number;
  longitude: number;
  region_ids: number[];
  product_ids: number[];
}

export interface EmployeeUpdateInput {
  first_name: string;
  last_name: string;
  email: string | null;
  mobile_phone: string | null;
  latitude: number;
  longitude: number;
  region_ids: number[];
  product_ids: number[];
}

export interface RescoSyncSummary {
  created: number;
  updated: number;
  skipped: number;
  failed: number;
  errors: string[];
}

export interface ServiceVisit {
  id: number;
  requested_date: string;
  status: VisitStatus;
  contract_line: ContractLine;
}

export interface Assignment {
  service_visit_id: number;
  employee_id: number;
  planned_start: string;
  planned_end: string;
  pinned: boolean;
  employee: Employee;
  service_visit: ServiceVisit;
}

export interface CreateAssignmentInput {
  service_visit_id: number;
  employee_id: number;
  planned_start: string;
}

export interface FreeSlot {
  employee_id: number;
  employee_name: string;
  start: string;
  end: string;
}

export interface AdHocVisitBookingInput {
  employee_id: number;
  start: string;
}

export interface ProposedAssignment {
  service_visit_id: number;
  employee_id: number;
  planned_start: string;
  planned_end: string;
  employee: Employee;
  service_visit: ServiceVisit;
}

export interface OptimizationProposal {
  scheduled: ProposedAssignment[];
  unscheduled_visit_ids: number[];
}

export interface OptimizeRunOptions {
  days_ahead: number;
  time_limit_seconds?: number;
}

export interface OptimizationApplyResult {
  created: Assignment[];
  skipped_visit_ids: number[];
}

export interface DrivingTimeComputeSummary {
  computed: number;
  skipped: number;
}

export interface ContractLineExtendSummary {
  lines_extended: number;
  visits_created: number;
}

export type LocationKind = "customer_location" | "employee";

export interface DayPlanningStop {
  kind: LocationKind;
  latitude: number;
  longitude: number;
  service_visit_id: number | null;
  customer_name: string | null;
  planned_start: string | null;
  planned_end: string | null;
}

export interface DayPlanningEmployeeRoute {
  employee_id: number;
  employee_name: string;
  stops: DayPlanningStop[];
  route: GeoPoint[];
}

export interface DayPlanningRoutes {
  employees: DayPlanningEmployeeRoute[];
}

export interface DemoScheduleRefreshSummary {
  days_shifted: number;
  visits_unassigned: number;
}
