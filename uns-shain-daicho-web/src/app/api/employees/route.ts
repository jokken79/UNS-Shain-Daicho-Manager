import { NextResponse } from 'next/server';
import { loadEmployees, getStats, getSalaryStats, getVisaAlerts, searchEmployees } from '@/lib/excel';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action');
  const query = searchParams.get('query');
  const days = searchParams.get('days');

  try {
    switch (action) {
      case 'stats':
        const stats = await getStats();
        return NextResponse.json(stats);
      
      case 'salary':
        const salaryStats = await getSalaryStats();
        return NextResponse.json(salaryStats);
      
      case 'visa':
        const visaDays = days ? parseInt(days, 10) : 90;
        const alerts = await getVisaAlerts(visaDays);
        return NextResponse.json(alerts);
      
      case 'search':
        if (!query) {
          return NextResponse.json({ error: 'Query required' }, { status: 400 });
        }
        const results = await searchEmployees(query);
        return NextResponse.json(results);
      
      case 'all':
      default:
        const employees = await loadEmployees();
        return NextResponse.json(employees);
    }
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    );
  }
}
