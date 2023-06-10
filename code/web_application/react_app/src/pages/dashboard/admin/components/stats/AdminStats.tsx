import { VStack } from "@chakra-ui/react";
import UserStats from "./user-stats/UserStats";

const AdminStats = () => {
  return (
    <VStack spacing={5}>
      <UserStats />
    </VStack>
  );
};

export default AdminStats;
