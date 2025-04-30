import React from "react";
import { Survey } from "survey-react-ui";
import "survey-core/defaultV2.min.css";
import { Model } from "survey-core";

const surveyJson = {
  title: "Khảo sát hài lòng nhân viên",
  description: "Vui lòng trả lời trung thực. Mọi thông tin đều được bảo mật.",
  locale: "vi",
  showProgressBar: "top",
  firstPageIsStarted: true,
  startSurveyText: "Bắt đầu",
  pages: [
    {
      name: "start",
      elements: [
        {
          type: "html",
          html: "<h3>Chào mừng bạn đến với khảo sát nhân sự của công ty HHD</h3>"
        }
      ]
    },
    {
      name: "page1",
      elements: [
        {
          type: "radiogroup",
          name: "team_satisfaction",
          title: "Bạn cảm thấy hài lòng với đội nhóm hiện tại ở mức nào?",
          isRequired: true,
          choices: [
            "Rất không hài lòng",
            "Không hài lòng",
            "Bình thường",
            "Hài lòng",
            "Rất hài lòng"
          ]
        },
        {
          type: "checkbox",
          name: "improvement_areas",
          title: "Bạn muốn cải thiện điều gì tại nơi làm việc?",
          isRequired: true,
          hasOther: true,
          choices: ["Lương", "Môi trường làm việc", "Cơ hội thăng tiến", "Đào tạo"]
        }
      ]
    }
  ]
};

const SurveyPage = () => {
  const survey = new Model(surveyJson);

  survey.onComplete.add((sender) => {
    const result = sender.data;
    fetch("http://localhost:3001/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(result)
    })
      .then((res) => res.json())
      .then((data) => {
        alert("Đã gửi khảo sát thành công!");
      })
      .catch((err) => {
        console.error("Lỗi gửi khảo sát:", err);
        alert("Gửi khảo sát thất bại. Vui lòng thử lại sau.");
      });
  });

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <Survey model={survey} />
    </div>
  );
};

export default SurveyPage;
