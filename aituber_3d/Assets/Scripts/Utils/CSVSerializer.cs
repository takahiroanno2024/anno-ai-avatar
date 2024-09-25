using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Aituber
{
    [System.Serializable]
    public class QuestionData
    {
        public string question;
        public string answer;
    }

    public static class CSVSerializer
    {
        public static List<QuestionData> Deserialize(string csvFilePath)
        {
            List<QuestionData> questions = new List<QuestionData>();
            try
            {
                using (StreamReader reader = new StreamReader(csvFilePath))
                {
                    // Skip the header line
                    reader.ReadLine();
                    string line;
                    while ((line = reader.ReadLine()) != null)
                    {
                        string[] values = line.Split(',');
                        if (values.Length >= 2)
                        {
                            QuestionData data = new QuestionData
                            {
                                question = values[0],
                                answer = values[1]
                            };
                            questions.Add(data);
                        }
                    }
                }
            }
            catch (Exception e)
            {
                Debug.LogError("Error reading CSV file: " + e.Message);
            }

            return questions;
        }
    }
}