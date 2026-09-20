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

export type ProductType = "TJN" | "PRD";

export interface Skill {
  id: number;
  name: string;
}

export interface SkillCreateInput {
  name: string;
}

export interface SkillUpdateInput {
  name: string;
}

export interface ServiceOrderType {
  id: number;
  name: string;
}

export interface ServiceOrderTypeCreateInput {
  name: string;
}

export interface ServiceOrderTypeUpdateInput {
  name: string;
}

export interface Product {
  id: number;
  number: string;
  product_type: ProductType;
  name: string;
  tripletex_id: number | null;
  resco_product_id: string | null;
  sync_warning: string | null;
  skills: Skill[];
  service_order_type: ServiceOrderType | null;
}

export interface ProductCreateInput {
  product_type: ProductType;
  number: string;
  name: string;
  skill_ids: number[];
  service_order_type_id: number | null;
}

export interface ProductUpdateInput {
  product_type: ProductType;
  number: string;
  name: string;
  skill_ids: number[];
  service_order_type_id: number | null;
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
  tripletex_id: number | null;
  resco_account_id: string | null;
  sync_warning: string | null;
}

export interface CustomerCreateInput {
  name: string;
}

export interface CustomerUpdateInput {
  name: string;
  email: string | null;
  phone_number: string | null;
  organization_number: string | null;
}

export interface CustomerLocation {
  id: number;
  address_line_1: string | null;
  address_line_2: string | null;
  postal_code: string | null;
  city: string | null;
  address: string;
  latitude: number | null;
  longitude: number | null;
  coordinates_locked: boolean;
  customer: Customer;
  region: Region | null;
  tripletex_id: number | null;
  resco_asset_id: string | null;
  sync_warning: string | null;
}

export interface CustomerLocationCoordinatesInput {
  latitude: number;
  longitude: number;
  coordinates_locked: boolean;
}

export interface CustomerLocationCreateInput {
  customer_id: number;
  address_line_1: string;
  address_line_2: string | null;
  postal_code: string | null;
  city: string | null;
}

export interface CustomerLocationUpdateInput {
  address_line_1: string;
  address_line_2: string | null;
  postal_code: string | null;
  city: string | null;
}

export type ContractLineIntervalUnit = "week" | "month" | "quarter";

export interface ContractLine {
  id: number;
  contract_id: number;
  start_date: string;
  end_date: string | null;
  interval_unit: ContractLineIntervalUnit;
  interval_count: number;
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
  interval_unit: ContractLineIntervalUnit;
  interval_count: number;
  duration_minutes: number;
  priority: number;
  required_product_ids: number[];
}

export interface ContractLineUpdateInput {
  customer_location_id: number;
  start_date: string;
  end_date: string | null;
  interval_unit: ContractLineIntervalUnit;
  interval_count: number;
  duration_minutes: number;
  priority: number;
  required_product_ids: number[];
}

export interface ContractLineIntervalOption {
  label: string;
  interval_unit: ContractLineIntervalUnit;
  interval_count: number;
}

export const CONTRACT_LINE_INTERVAL_OPTIONS: ContractLineIntervalOption[] = [
  { label: "Every week", interval_unit: "week", interval_count: 1 },
  { label: "Every 2 weeks", interval_unit: "week", interval_count: 2 },
  { label: "Every 3 weeks", interval_unit: "week", interval_count: 3 },
  { label: "Every 4 weeks", interval_unit: "week", interval_count: 4 },
  { label: "Every month", interval_unit: "month", interval_count: 1 },
  { label: "Every 2 months", interval_unit: "month", interval_count: 2 },
  { label: "Every 3 months", interval_unit: "month", interval_count: 3 },
  { label: "Every quarter", interval_unit: "quarter", interval_count: 1 },
];

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
  skills: Skill[];
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
  skill_ids: number[];
}

export interface EmployeeUpdateInput {
  first_name: string;
  last_name: string;
  email: string | null;
  mobile_phone: string | null;
  latitude: number;
  longitude: number;
  region_ids: number[];
  skill_ids: number[];
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
  required_skills: Skill[];
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
  execution_mode?: "single" | "parallel";
  plan_from_time?: string;
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

export interface User {
  id: number;
  email: string;
  is_admin: boolean;
  customer_ids: number[];
}

export interface UserCreateInput {
  email: string;
  password: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export type CurrentUser = User | null;

export interface UserCustomersInput {
  customer_ids: number[];
}

export type ServiceRequestStatus = "pending" | "acknowledged";

export interface ServiceRequest {
  id: number;
  customer: Customer;
  customer_location: CustomerLocation;
  product: Product;
  note: string | null;
  status: ServiceRequestStatus;
  created_at: string;
}

export interface ServiceRequestCreateInput {
  customer_id: number;
  customer_location_id: number;
  product_id: number;
  note: string | null;
}

export interface CustomerDashboard {
  customer: Customer;
  customer_locations: CustomerLocation[];
  contracts: Contract[];
  upcoming_visits: ServiceVisit[];
}
