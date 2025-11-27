import { useState, useRef } from "react";
import { ChevronRight, Upload } from "lucide-react";
import evaluateChartData from "../assets/evaluate_chart.csv?raw";

interface SkillData {
  category: string;
  subcategory: string;
  skill_name: string;
  level: string;
  weighted_score: number;
  description: string;
  evidence_examples: string;
  developer_type: string;
}

interface SkillDetail {
  name: string;
  level: string;
  weighted_score: number;
  description: string;
  evidence_examples: string;
}

interface SkillDetailModalProps {
  open: boolean;
  onClose: () => void;
  skill: SkillDetail | null;
}

function SkillDetailModal({ open, onClose, skill }: SkillDetailModalProps) {
  if (!open || !skill) return null;

  const getLevelColor = (level: string) => {
    switch (level) {
      case "Basic":
        return "bg-green-100 text-green-800 border-green-300";
      case "Intermediate":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "Advanced":
        return "bg-red-100 text-red-800 border-red-300";
      default:
        return "bg-slate-100 text-slate-800 border-slate-300";
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-slate-900">{skill.name}</h2>
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium border ${getLevelColor(
                skill.level
              )}`}
            >
              {skill.level}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 text-2xl w-8 h-8"
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div className="p-4 bg-slate-50 rounded-lg">
            <p className="text-sm text-slate-600 mb-1">Weighted Score</p>
            <p className="text-2xl font-medium text-indigo-600">
              {skill.weighted_score}점
            </p>
          </div>

          <div>
            <h4 className="text-sm font-medium text-slate-900 mb-2">설명</h4>
            <p className="text-slate-700 p-3 bg-slate-50 rounded-lg">
              {skill.description}
            </p>
          </div>

          <div>
            <h4 className="text-sm font-medium text-slate-900 mb-2">
              증거 예시
            </h4>
            <p className="text-slate-700 p-3 bg-indigo-50 rounded-lg">
              {skill.evidence_examples}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

interface SkillTableProps {
  skills: SkillData[];
  onSkillClick: (skill: SkillDetail) => void;
}

function SkillTable({ skills, onSkillClick }: SkillTableProps) {
  const skillGroups = skills.reduce((acc, skill) => {
    if (!acc[skill.skill_name]) {
      acc[skill.skill_name] = [];
    }
    acc[skill.skill_name].push(skill);
    return acc;
  }, {} as Record<string, SkillData[]>);

  const getLevelBadgeClass = (level: string) => {
    switch (level) {
      case "Basic":
        return "bg-green-100 text-green-700 border-green-300";
      case "Intermediate":
        return "bg-amber-100 text-amber-700 border-amber-300";
      case "Advanced":
        return "bg-red-100 text-red-700 border-red-300";
      default:
        return "bg-slate-100 text-slate-700 border-slate-300";
    }
  };

  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="w-full">
        <thead className="bg-slate-100">
          <tr>
            <th className="text-left p-3 text-sm font-medium text-slate-700">
              스킬명
            </th>
            <th className="text-center p-3 text-sm font-medium text-green-700 w-1/4">
              Basic
            </th>
            <th className="text-center p-3 text-sm font-medium text-amber-700 w-1/4">
              Intermediate
            </th>
            <th className="text-center p-3 text-sm font-medium text-red-700 w-1/4">
              Advanced
            </th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(skillGroups).map(([skillName, skillLevels]) => (
            <tr key={skillName} className="border-t hover:bg-slate-50">
              <td className="p-3 font-medium text-slate-800">{skillName}</td>
              {["Basic", "Intermediate", "Advanced"].map((level) => {
                const skillData = skillLevels.find((s) => s.level === level);
                return (
                  <td key={level} className="p-3 text-center">
                    {skillData ? (
                      <button
                        onClick={() =>
                          onSkillClick({
                            name: skillName,
                            level: skillData.level,
                            weighted_score: skillData.weighted_score,
                            description: skillData.description,
                            evidence_examples: skillData.evidence_examples,
                          })
                        }
                        className="inline-flex flex-col items-center gap-1 px-3 py-2 rounded-lg hover:bg-slate-100 transition-colors w-full"
                      >
                        <span className="text-sm font-medium text-slate-900">
                          {skillData.weighted_score}점
                        </span>
                        <span
                          className={`${getLevelBadgeClass(
                            level
                          )} text-xs px-2 py-0.5 rounded border`}
                        >
                          클릭하여 상세보기
                        </span>
                      </button>
                    ) : (
                      <span className="text-slate-400 text-sm">-</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface AccordionItemProps {
  category: string;
  subcategories: Record<string, SkillData[]>;
  onSkillClick: (skill: SkillDetail) => void;
  isOpen: boolean;
  onToggle: () => void;
}

function AccordionItem({
  category,
  subcategories,
  onSkillClick,
  isOpen,
  onToggle,
}: AccordionItemProps) {
  return (
    <div className="border rounded-lg overflow-hidden bg-white shadow-sm">
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 hover:bg-slate-50 transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-indigo-600"></div>
          <span className="font-medium text-slate-900">{category}</span>
          <span className="ml-2 px-2 py-0.5 text-xs border border-slate-300 rounded text-slate-600">
            {Object.keys(subcategories).length} 하위 카테고리
          </span>
        </div>
        <ChevronRight
          className={`text-slate-400 transition-transform duration-300 w-5 h-5 ${
            isOpen ? "rotate-90" : ""
          }`}
        />
      </button>

      <div
        className={`transition-all duration-300 ease-in-out overflow-hidden ${
          isOpen ? "max-h-[5000px] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="px-6 pb-4 space-y-3">
          {Object.entries(subcategories).map(([subcategory, skills]) => (
            <SubAccordionItem
              key={subcategory}
              subcategory={subcategory}
              skills={skills}
              onSkillClick={onSkillClick}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface SubAccordionItemProps {
  subcategory: string;
  skills: SkillData[];
  onSkillClick: (skill: SkillDetail) => void;
}

function SubAccordionItem({
  subcategory,
  skills,
  onSkillClick,
}: SubAccordionItemProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border rounded-lg overflow-hidden bg-slate-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 hover:bg-slate-100 transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-indigo-400"></div>
          <span className="text-slate-800">{subcategory}</span>
          <span className="ml-2 px-2 py-0.5 text-xs bg-slate-200 rounded text-slate-600">
            {new Set(skills.map((s) => s.skill_name)).size} 스킬
          </span>
        </div>
        <ChevronRight
          className={`text-slate-400 transition-transform duration-300 w-5 h-5 ${
            isOpen ? "rotate-90" : ""
          }`}
        />
      </button>

      <div
        className={`transition-all duration-300 ease-in-out overflow-hidden ${
          isOpen ? "max-h-[3000px] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="px-4 pb-4">
          <SkillTable skills={skills} onSkillClick={onSkillClick} />
        </div>
      </div>
    </div>
  );
}

export default function EvaluateChart() {
  const [selectedSkill, setSelectedSkill] = useState<SkillDetail | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [openCategories, setOpenCategories] = useState<Set<string>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Parse CSV data
  const parseCSV = (csv: string): SkillData[] => {
    const lines = csv.trim().split("\n");

    return lines.slice(1).map((line) => {
      const values = line.split(",");
      return {
        category: values[0],
        subcategory: values[1],
        skill_name: values[2],
        level: values[3],
        weighted_score: parseInt(values[4]),
        description: values[5],
        evidence_examples: values[6],
        developer_type: values[7],
      };
    });
  };

  const skillData = parseCSV(evaluateChartData);

  // Group data by category and subcategory
  const groupedData = skillData.reduce((acc, skill) => {
    if (!acc[skill.category]) {
      acc[skill.category] = {};
    }
    if (!acc[skill.category][skill.subcategory]) {
      acc[skill.category][skill.subcategory] = [];
    }
    acc[skill.category][skill.subcategory].push(skill);
    return acc;
  }, {} as Record<string, Record<string, SkillData[]>>);

  const handleSkillClick = (skill: SkillDetail) => {
    setSelectedSkill(skill);
    setModalOpen(true);
  };

  const toggleCategory = (category: string) => {
    setOpenCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // TODO: CSV 파일 업로드 처리 로직 구현
      console.log("선택된 파일:", file.name);
      alert(`평가기준이 업데이트 되었습니다.\n`);
      // 파일 입력 초기화
      event.target.value = "";
    }
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-50 to-indigo-50/30">
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-5xl mx-auto">
          {/* Page Header */}
          <div className="mb-12 text-center">
            <h1 className="text-4xl font-bold text-slate-900 mb-4">
              평가 기준
            </h1>
            <p className="text-lg text-slate-600">
              Sesami는 평가기준표를 기반으로 지원자의 역량을 종합적으로
              분석합니다
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {/* Content Card */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="border-b bg-linear-to-r from-indigo-50 to-purple-50 px-8 py-6">
              <div className="flex items-center justify-between gap-4 mb-6">
                <h2 className="text-2xl font-bold text-slate-900">
                  상세 스킬 평가 기준
                </h2>
                <button
                  onClick={handleUploadClick}
                  className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors shadow-md hover:shadow-lg whitespace-nowrap shrink-0"
                >
                  <Upload className="w-5 h-5" />
                  <span className="font-medium">평가기준표 업데이트</span>
                </button>
              </div>
              <p className="text-sm text-slate-600">
                각 스킬은 Basic, Intermediate, Advanced 레벨로 평가되며,
                가중치가 적용된 점수를 부여합니다. 셀을 클릭하면 상세한 평가
                기준을 확인할 수 있습니다.
              </p>
            </div>

            <div className="p-6">
              <div className="space-y-4">
                {Object.entries(groupedData).map(
                  ([category, subcategories]) => (
                    <AccordionItem
                      key={category}
                      category={category}
                      subcategories={subcategories}
                      onSkillClick={handleSkillClick}
                      isOpen={openCategories.has(category)}
                      onToggle={() => toggleCategory(category)}
                    />
                  )
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <SkillDetailModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        skill={selectedSkill}
      />
    </div>
  );
}
