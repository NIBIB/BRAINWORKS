import { Box } from "@chakra-ui/react";
import { Component } from "react";
import Chart from "react-apexcharts";
import { brand100, brand500 } from "../../../../setup/theme/colors";

const LABEL = "Trends in Neuroplaciticity research by subject of study";
export default class BarChart extends Component {
  constructor(props) {
    super(props);

    this.state = {
      series: [
        {
          name: "Humans",
          data: [1, 20, 95, 200, 110],
        },
        {
          name: "Animals",
          data: [10, 110, 300, 690, 350],
        },
      ],
      options: {
        dataLabels: {
          enabled: false,
        },
        title: {
          text: LABEL,
          align: "left",
          margin: 10,
          offsetX: 0,
          offsetY: 0,
          floating: false,
          style: {
            fontSize: "14px",
            fontWeight: "bold",
            fontFamily: undefined,
            color: "#263238",
          },
        },
        colors: [brand500, brand100],
        chart: {
          type: "bar",
          height: 350,
          stacked: true,
          toolbar: {
            show: false,
          },
          zoom: {
            enabled: true,
          },
        },
        responsive: [
          {
            breakpoint: 1000,
            options: {
              legend: {
                position: "bottom",
                offsetX: -10,
                offsetY: 0,
              },
            },
          },
        ],
        plotOptions: {
          bar: {
            horizontal: false,
            borderRadius: 10,
          },
        },
        xaxis: {
          type: "datetime",
          categories: ["1980", "1990", "2000", "2010", "2020"],
        },
        legend: {
          position: "right",
          offsetY: 40,
        },
        fill: {
          opacity: 1,
        },
        ...this.props.options,
      },
    };
  }
  render() {
    return (
      <Box
        width={"100%"}
        height={"100%"}
        bg={"white"}
        border={"1px"}
        borderColor={"gray.300"}
        padding={2}
        boxShadow={"md"}
      >
        <Chart
          options={this.state.options}
          series={this.state.series}
          type="bar"
          width={"100%"}
          height={"100%"}
        />
      </Box>
    );
  }
}
