import { Box, Divider, Heading, HStack, Stack, VStack } from "@chakra-ui/react";
import { faker } from "@faker-js/faker";
import ReactChart from "../../../../../../common/components/Charts/ReactChart";
import TripleTimeline from "./FrequencyTimeline";

const FrequencyTimelines = () => {
  // * Generate random dataset
  // * Generate years & triple timeline
  const num_data = 40;

  let years: number[] = [];
  let triples: string[] = [];
  let timelines: any = [];
  let start = 1980;
  for (let i = 0; i < num_data; i++) {
    let timeline: any = { label: start.toString(), data: [] };
    years[i] = start;
    for (let i = 0; i < num_data; i++) {
      timeline.data[i] = Math.floor(Math.random() * 100);
    }
    start++;
    timelines[i] = timeline;
    triples[i] = faker.random.words();
  }

  let random: any = {
    itemLabel: "Triples",
    timelineLabel: "Frequency timeline",
    years: years,
    timelines: timelines,
    triples: triples,
  };
  console.log(random);

  return (
    <Box h="100vh">
      <Stack w="100%" h="100%" justify="center" align="center">
        {/* Timeline labels */}
        <VStack
          spacing={0}
          align="flex-start"
          w="90vw"
          overflowX="auto"
          h={triples.length <= 3 ? "auto" : "90%"}
          pt={5}
          boxShadow="lg"
          borderRadius="lg"
          bg="white"
          m={50}
        >
          {/* Labels */}
          <HStack w="100%" pb={5}>
            <Heading fontSize="sm" w="150px" pl={3}>
              {random.itemLabel}
            </Heading>
            <Heading fontSize="sm">
              {random.timelineLabel} ({years[0]} - {years[years.length - 1]})
            </Heading>
          </HStack>
          {/* Determine length based on minimum number of years  */}
          <Box
            w={years.length < 30 ? "100%" : years.length * 50}
            overflowX="scroll"
          >
            <Divider />
            {/* Empty chart to display years, very hacky */}
            <Box h="65px" pt="15px" pl="150px" bg="gray.50" pos="sticky">
              <ReactChart
                chartXAxis={years}
                chartDatasets={[]}
                chartType={"line"}
                chartOptions={{
                  scales: {
                    x: {
                      position: "top",
                      ticks: {
                        display: true,
                      },
                      grid: {
                        display: false,
                        drawBorder: false,
                      },
                    },
                  },
                  y: {
                    grid: {
                      display: false,
                      drawBorder: false,
                    },
                  },
                }}
              />
            </Box>
            <Divider />
            {/* Timeline rows */}
            <VStack h="90%" w="100%">
              {timelines.map((_timeline: any, i: number) => {
                return (
                  <>
                    <TripleTimeline
                      triples={triples}
                      label={triples[i]}
                      data={timelines[i].data}
                      years={years}
                    />
                    {i < timelines.length - 1 && <Divider />}
                  </>
                );
              })}
            </VStack>
          </Box>
        </VStack>
      </Stack>
    </Box>
  );
};
export default FrequencyTimelines;
