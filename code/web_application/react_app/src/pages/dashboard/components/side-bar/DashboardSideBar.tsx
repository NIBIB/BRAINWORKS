import { ReactNode } from "react";
import { FiActivity, FiHome, FiUser } from "react-icons/fi";
import FilterSidebar from "../../../../common/components/Sidebar";

export const DASHBOARD_SIDEBAR_ITEMS = [
  {
    title: "",
    items: [
      // { name: "Create", icon: FiHome, component: <Create />, path: "/" },
      {
        name: "Account",
        icon: FiUser,
        path: "/account",
      },
      {
        name: "Admin",
        icon: FiActivity,
        path: "/admin",
        admin: true,
      },
    ],
  },
];

interface AppProps {
  children: ReactNode;
}

const DashboardSideBar = ({ children }: AppProps) => {
  return (
    <FilterSidebar sidebarItems={DASHBOARD_SIDEBAR_ITEMS} initalState={"Home"}>
      {children}
    </FilterSidebar>
  );
};

export default DashboardSideBar;
