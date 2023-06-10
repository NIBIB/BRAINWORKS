import { Box, Container } from "@chakra-ui/react";
import PageHeader from "common/components/PageHeader";
import MenuTab from "../../../common/components/MenuTabs";
import usePageTitle from "../../../common/hooks/usePageTitle";
import AdminStats from "./components/stats/AdminStats";
import UserManager from "./components/user-manager/UserManager";

export const ADMIN_MENU_ITEMS = [
  { name: "Overview", component: <AdminStats /> },
  { name: "Manage", component: <UserManager /> },
];

const Admin = () => {
  usePageTitle("Admin");
  return (
    <Box py={100}>
      <PageHeader
        subTitle={"Manage"}
        title={"Administrator"}
        desc={"Manage users or view site statistics"}
        stackProps={{ pb: 50 }}
      />
      <Container maxW="6xl">
        <MenuTab items={ADMIN_MENU_ITEMS} />
      </Container>
    </Box>
  );
};

export default Admin;
