'use client';

import { useState, useEffect } from 'react';
import { Employee, EmployeeStats, VisaAlert } from '@/types';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { Users, AlertTriangle, TrendingUp, Building2, Search, Download, RefreshCw } from 'lucide-react';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function Dashboard() {
  const [stats, setStats] = useState<EmployeeStats | null>(null);
  const [alerts, setAlerts] = useState<VisaAlert[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [statsRes, alertsRes, employeesRes] = await Promise.all([
        fetch('/api/employees?action=stats'),
        fetch('/api/employees?action=visa&days=90'),
        fetch('/api/employees?action=all')
      ]);
      
      setStats(await statsRes.json());
      setAlerts(await alertsRes.json());
      setEmployees(await employeesRes.json());
    } catch (error) {
      console.error('Failed to load data:', error);
    }
    setLoading(false);
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const res = await fetch(`/api/employees?action=search&query=${encodeURIComponent(searchQuery)}`);
      const results = await res.json();
      setEmployees(results);
    } catch (error) {
      console.error('Search failed:', error);
    }
    setLoading(false);
  }

  const categoryData = stats ? Object.entries(stats.byCategory).map(([name, value]) => ({ name, value })) : [];
  const nationalityData = stats ? Object.entries(stats.byNationality).map(([name, value]) => ({ name, value })).slice(0, 10) : [];
  const ageData = stats ? Object.entries(stats.ageGroups).map(([name, value]) => ({ name, value })) : [];

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Users className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">UNS 社員台帳</h1>
            </div>
            <form onSubmit={handleSearch} className="flex items-center space-x-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="氏名・カナで検索..."
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button type="submit" className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Search className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">総従業員数</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.total || 0}</p>
              </div>
              <Users className="w-10 h-10 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">在職中</p>
                <p className="text-3xl font-bold text-green-600">{stats?.active || 0}</p>
              </div>
              <TrendingUp className="w-10 h-10 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">退社</p>
                <p className="text-3xl font-bold text-gray-600">{stats?.retired || 0}</p>
              </div>
              <Users className="w-10 h-10 text-gray-400" />
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">ビザ期限</p>
                <p className="text-3xl font-bold text-orange-600">{alerts.length}</p>
              </div>
              <AlertTriangle className="w-10 h-10 text-orange-500" />
            </div>
          </div>
        </div>

        {/* Visa Alerts */}
        {alerts.length > 0 && (
          <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 mb-6">
            <div className="flex items-center space-x-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              <h2 className="text-lg font-semibold text-orange-900">ビザ期限アラート</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {alerts.slice(0, 6).map((alert, idx) => (
                <div 
                  key={idx}
                  className={`p-3 rounded-lg ${
                    alert.alertLevel === 'expired' ? 'bg-red-100 border-red-300' :
                    alert.alertLevel === 'urgent' ? 'bg-red-50 border-red-200' :
                    alert.alertLevel === 'warning' ? 'bg-orange-50 border-orange-200' :
                    'bg-yellow-50 border-yellow-200'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{alert.employee.name}</span>
                    <span className={`text-sm ${
                      alert.alertLevel === 'expired' ? 'text-red-600' :
                      alert.alertLevel === 'urgent' ? 'text-red-500' :
                      alert.alertLevel === 'warning' ? 'text-orange-500' :
                      'text-yellow-600'
                    }`}>
                      {alert.daysUntilExpiry}日
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">{alert.employee.visaType}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Category Distribution */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">分類別推移</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={categoryData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {categoryData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Age Distribution */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">年齢分布</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={ageData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Companies */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Building2 className="w-5 h-5 mr-2" />
            派遣先 TOP 10
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart 
              data={Object.entries(stats?.byCompany || {})
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .map(([name, value]) => ({ name, value }))}
              layout="vertical"
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={120} />
              <Tooltip />
              <Bar dataKey="value" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Employees Table */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">従業員一覧</h3>
            <button className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              <Download className="w-4 h-4" />
              <span>エクスポート</span>
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">№</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">氏名</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">カナ</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">分類</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">状態</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">派遣先</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">年齢</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">時給</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {employees.slice(0, 50).map((emp) => (
                  <tr key={emp.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{emp.no}</td>
                    <td className="px-4 py-3 text-sm font-medium">{emp.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{emp.kana}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        emp.category === '派遣' ? 'bg-blue-100 text-blue-800' :
                        emp.category === '請負' ? 'bg-green-100 text-green-800' :
                        emp.category === 'Staff' ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {emp.category}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        emp.status === '在職中' ? 'bg-green-100 text-green-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {emp.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{emp.company || '-'}</td>
                    <td className="px-4 py-3 text-sm">{emp.age || '-'}</td>
                    <td className="px-4 py-3 text-sm">¥{emp.hourlyWage?.toLocaleString() || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {employees.length > 50 && (
            <p className="text-sm text-gray-500 mt-4 text-center">
              {employees.length} 件中 51 件を表示
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
