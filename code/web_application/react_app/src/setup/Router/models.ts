export interface routeItem {
  path: string[];
  name: string;
  hide?: boolean;
  type: "external" | "internal" | "none";
  admin?: boolean;
}
